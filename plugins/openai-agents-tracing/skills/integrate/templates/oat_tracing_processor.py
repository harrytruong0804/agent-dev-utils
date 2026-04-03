"""Custom TracingProcessor that exports OpenAI Agent SDK traces to the
OAT dashboard (https://github.com/harrytruong0804/openai-agents-tracing).

Converts SDK Trace/Span objects into the dashboard's ingestion format and POSTs
them to the /traces/event endpoint.

Docker images: noitq/oat-api, noitq/oat-client
"""

import logging
import threading
from typing import Any

import httpx
from agents.tracing import TracingProcessor, Trace, Span

logger = logging.getLogger(__name__)


def _safe_json_serialize(obj: Any) -> Any:
    """Recursively convert non-serializable objects to strings."""
    if isinstance(obj, dict):
        return {k: _safe_json_serialize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_safe_json_serialize(v) for v in obj]
    if isinstance(obj, (str, int, float, bool, type(None))):
        return obj
    return str(obj)


DEFAULT_WORKFLOW_NAME = "agent-workflow"


class OpenAIAgentsTracingDashboardProcessor(TracingProcessor):
    """Bridges the OpenAI Agent SDK tracing API to the self-hosted OAT dashboard.

    Collects spans synchronously during agent execution, then flushes
    the complete trace + spans to the dashboard API when each trace ends.
    """

    def __init__(
        self,
        api_url: str,
        api_key: str,
        timeout: float = 10.0,
        workflow_name: str = DEFAULT_WORKFLOW_NAME,
    ) -> None:
        self._api_url = api_url.rstrip("/")
        self._api_key = api_key
        self._timeout = timeout
        self._workflow_name = workflow_name

        self._trace_spans: dict[str, list[dict[str, Any]]] = {}
        self._orphan_spans: dict[str, list[dict[str, Any]]] = {}
        self._lock = threading.Lock()

        self._client = httpx.Client(
            timeout=timeout,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
        )

    def on_trace_start(self, trace: Trace) -> None:
        trace_id = trace.trace_id
        with self._lock:
            self._trace_spans[trace_id] = []
            orphans = self._orphan_spans.pop(trace_id, [])
            if orphans:
                self._trace_spans[trace_id].extend(orphans)

    def on_trace_end(self, trace: Trace) -> None:
        trace_id = trace.trace_id

        with self._lock:
            spans = self._trace_spans.pop(trace_id, [])

        # Aggregate child response/generation usage into parent agent spans
        self._aggregate_agent_usage(spans)

        try:
            trace_export = trace.export()
        except Exception:
            logger.error("Trace export failed for %s", trace_id, exc_info=True)
            trace_export = {}

        trace_event: dict[str, Any] = {
            "object": "trace",
            "id": trace_id,
            "workflow_name": trace_export.get("name", self._workflow_name),
            "group_id": trace_export.get("group_id"),
            "metadata": trace_export.get("metadata") or {},
        }

        payload: dict[str, Any] = {
            "data": [trace_event] + spans,
        }

        try:
            resp = self._client.post(
                f"{self._api_url}/traces/event",
                json=payload,
            )
            if resp.status_code != 201:
                logger.warning(
                    "OAT dashboard API error: status=%d trace_id=%s",
                    resp.status_code,
                    trace_id,
                )
        except Exception:
            logger.error("Failed to export trace %s", trace_id, exc_info=True)

    def on_span_start(self, span: "Span[Any]") -> None:
        pass

    def on_span_end(self, span: "Span[Any]") -> None:
        # Extract rich data from span_data BEFORE export() (which discards it)
        live_span_data = getattr(span, "span_data", None)
        response_extra: dict[str, Any] | None = None
        if live_span_data and getattr(live_span_data, "type", None) == "response":
            response_extra = self._extract_response_data(live_span_data)

        try:
            exported = span.export()
        except Exception:
            return

        trace_id = exported.get("trace_id", "")
        span_id = exported.get("id", "") or exported.get("span_id", "")

        raw_span_data = exported.get("span_data", {})
        if hasattr(raw_span_data, "export"):
            try:
                span_data_dict = raw_span_data.export()
            except Exception:
                span_data_dict = {"type": getattr(raw_span_data, "type", "unknown")}
        elif isinstance(raw_span_data, dict):
            span_data_dict = raw_span_data
        else:
            span_data_dict = {"raw": str(raw_span_data)}

        # Merge rich response data into span_data
        if response_extra and isinstance(span_data_dict, dict):
            span_data_dict.update(response_extra)

        span_data_dict = _safe_json_serialize(span_data_dict)

        span_event: dict[str, Any] = {
            "object": "trace.span",
            "id": span_id,
            "trace_id": trace_id,
            "parent_id": exported.get("parent_id"),
            "started_at": exported.get("started_at"),
            "ended_at": exported.get("ended_at"),
            "span_data": span_data_dict,
            "error": _safe_json_serialize(exported.get("error")),
        }

        with self._lock:
            if trace_id in self._trace_spans:
                self._trace_spans[trace_id].append(span_event)
            else:
                self._orphan_spans.setdefault(trace_id, []).append(span_event)

    def shutdown(self) -> None:
        self.force_flush()
        self._client.close()

    def force_flush(self) -> None:
        with self._lock:
            remaining = dict(self._trace_spans)
            self._trace_spans.clear()
            orphans = dict(self._orphan_spans)
            self._orphan_spans.clear()

        for trace_id, spans in remaining.items():
            if not spans:
                continue
            self._flush_spans(trace_id, spans)

        for trace_id, spans in orphans.items():
            if not spans:
                continue
            self._flush_spans(trace_id, spans, workflow=f"{self._workflow_name}-orphans")

    @staticmethod
    def _extract_response_data(span_data: Any) -> dict[str, Any]:
        """Extract model, usage, reasoning, and output from a ResponseSpanData."""
        extra: dict[str, Any] = {}
        response = getattr(span_data, "response", None)
        if response is None:
            return extra

        # Model name
        model = getattr(response, "model", None)
        if model:
            extra["model"] = model

        # Token usage
        usage = getattr(response, "usage", None)
        if usage:
            usage_dict: dict[str, Any] = {
                "input_tokens": getattr(usage, "input_tokens", 0),
                "output_tokens": getattr(usage, "output_tokens", 0),
                "total_tokens": getattr(usage, "total_tokens", 0),
            }

            # Detailed token breakdown (cached input, reasoning output)
            # OAT frontend reads: usage.input_tokens_details.cached_tokens
            #                     usage.output_tokens_details.reasoning_tokens
            input_details = getattr(usage, "input_tokens_details", None)
            if input_details:
                cached = getattr(input_details, "cached_tokens", 0)
                if cached:
                    usage_dict["input_tokens_details"] = {"cached_tokens": cached}

            output_details = getattr(usage, "output_tokens_details", None)
            if output_details:
                reasoning = getattr(output_details, "reasoning_tokens", 0)
                if reasoning:
                    usage_dict["output_tokens_details"] = {"reasoning_tokens": reasoning}

            extra["usage"] = usage_dict

        # Output items — extract text content and reasoning summaries
        output_items = getattr(response, "output", None) or []
        output_texts: list[str] = []
        reasoning_texts: list[str] = []
        tool_calls: list[dict[str, Any]] = []

        for item in output_items:
            item_type = getattr(item, "type", "")

            if item_type == "message":
                for content in getattr(item, "content", []):
                    if getattr(content, "type", "") == "output_text":
                        text = getattr(content, "text", "")
                        if text:
                            output_texts.append(text)

            elif item_type == "reasoning":
                for summary in getattr(item, "summary", []):
                    text = getattr(summary, "text", "")
                    if text:
                        reasoning_texts.append(text)

            elif item_type == "function_call":
                tool_calls.append({
                    "name": getattr(item, "name", ""),
                    "arguments": getattr(item, "arguments", ""),
                    "call_id": getattr(item, "call_id", ""),
                })

        if output_texts:
            extra["output"] = "\n".join(output_texts)
        if reasoning_texts:
            extra["reasoning"] = "\n".join(reasoning_texts)
        if tool_calls:
            extra["tool_calls"] = tool_calls

        # Input — only keep the last message to avoid huge payloads
        input_data = getattr(span_data, "input", None)
        if input_data:
            if isinstance(input_data, str):
                extra["input"] = input_data
            elif isinstance(input_data, list) and input_data:
                last = input_data[-1]
                if isinstance(last, dict):
                    serialized_last = last
                elif hasattr(last, "model_dump"):
                    serialized_last = last.model_dump(exclude_none=True)
                elif hasattr(last, "dict"):
                    serialized_last = last.dict(exclude_none=True)
                else:
                    serialized_last = str(last)
                extra["input"] = serialized_last
                extra["input_count"] = len(input_data)

        return extra

    @staticmethod
    def _aggregate_agent_usage(spans: list[dict[str, Any]]) -> None:
        """Roll up token usage from child response/generation spans into agent spans.

        Mutates agent spans in-place, adding a ``usage`` key to their ``span_data``
        so the OAT frontend can display totals when an agent item is clicked.
        """
        span_by_id: dict[str, dict[str, Any]] = {s["id"]: s for s in spans if s.get("id")}
        agent_usage: dict[str, dict[str, int]] = {}

        for span in spans:
            span_data = span.get("span_data") or {}
            span_type = span_data.get("type", "")

            if span_type not in ("response", "generation"):
                continue
            usage = span_data.get("usage")
            if not usage:
                continue

            parent_id = span.get("parent_id")
            while parent_id:
                parent = span_by_id.get(parent_id)
                if not parent:
                    break
                parent_data = parent.get("span_data") or {}
                if parent_data.get("type") == "agent":
                    if parent_id not in agent_usage:
                        agent_usage[parent_id] = {
                            "input_tokens": 0,
                            "output_tokens": 0,
                            "total_tokens": 0,
                            "cached_tokens": 0,
                            "reasoning_tokens": 0,
                        }
                    totals = agent_usage[parent_id]
                    totals["input_tokens"] += usage.get("input_tokens", 0)
                    totals["output_tokens"] += usage.get("output_tokens", 0)
                    totals["total_tokens"] += usage.get("total_tokens", 0)
                    input_details = usage.get("input_tokens_details") or {}
                    totals["cached_tokens"] += input_details.get("cached_tokens", 0)
                    output_details = usage.get("output_tokens_details") or {}
                    totals["reasoning_tokens"] += output_details.get("reasoning_tokens", 0)
                    break
                parent_id = parent.get("parent_id")

        for agent_id, totals in agent_usage.items():
            agent_span = span_by_id[agent_id]
            usage_dict: dict[str, Any] = {
                "input_tokens": totals["input_tokens"],
                "output_tokens": totals["output_tokens"],
                "total_tokens": totals["total_tokens"],
            }
            if totals["cached_tokens"]:
                usage_dict["input_tokens_details"] = {"cached_tokens": totals["cached_tokens"]}
            if totals["reasoning_tokens"]:
                usage_dict["output_tokens_details"] = {"reasoning_tokens": totals["reasoning_tokens"]}
            agent_span.setdefault("span_data", {})["usage"] = usage_dict

    def _flush_spans(
        self, trace_id: str, spans: list[dict[str, Any]], workflow: str | None = None
    ) -> None:
        payload: dict[str, Any] = {
            "data": [
                {
                    "object": "trace",
                    "id": trace_id,
                    "workflow_name": workflow or self._workflow_name,
                    "group_id": None,
                    "metadata": {},
                }
            ]
            + spans,
        }
        try:
            self._client.post(f"{self._api_url}/traces/event", json=payload)
        except Exception:
            logger.error("Failed to flush trace %s", trace_id, exc_info=True)
