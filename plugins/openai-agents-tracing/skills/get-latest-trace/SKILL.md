---
name: get-latest-trace
description: Fetch a trace from the running OAT dashboard by ID and analyze the LLM + tools execution flow, token usage, reasoning, and self-corrections.
argument-hint: "<trace_id>"
---

# Get Trace

Fetch and analyze a trace from the running OAT (OpenAI Agents Tracing) dashboard.

## Arguments

- `trace_id` (required): The trace ID to fetch (e.g., `trace_799345e506d9401ab5a12d703279879c`).

## Prerequisites

The following env vars must be set (check `.env` or environment):
- `OAT_DASHBOARD_API_URL` — OAT API base URL (e.g., `http://localhost:3801`)
- `OAT_DASHBOARD_API_KEY` — API key (starts with `ak_`)

If any are missing, inform the user which vars are needed and stop.

## Execution Steps

### 1. Read credentials from environment

Read the project's `.env` file to get `OAT_DASHBOARD_API_URL` and `OAT_DASHBOARD_API_KEY`.

### 2. Fetch trace by ID

```bash
curl -s "${OAT_DASHBOARD_API_URL}/traces/${trace_id}" \
  -H "Authorization: Bearer ${OAT_DASHBOARD_API_KEY}"
```

The detail endpoint returns the trace with all spans joined (via MongoDB `$lookup`) under the `data` key.

### 3. Analyze and present the trace

Parse the trace response (`data` key) which contains:
- `id`, `workflow_name`, `createdAt` — trace metadata
- `spans[]` — array of span objects, each with:
  - `span_data.type` — one of: `agent`, `response`, `function`, `mcp_tools`
  - `parent_id` — forms the span tree
  - `started_at`, `ended_at` — timing
  - `span_data` — type-specific data (see below)

**Build and display an execution flow using this format:**

```
## Trace: {trace_id}
**Time:** {started} → {ended} ({duration}s)
**User Query:** "{input from first response span}"

### Execution Flow

┌─ Phase 1: MCP Discovery ({duration})
│  ① mcp_tools [server_name] → [tool_list]
│  ...
│
├─ Phase 2: LLM Call #N ({duration})
│  Model: {model}
│  Tokens: {input} in ({cached} cached) / {output} out ({reasoning} reasoning)
│  ★ Reasoning: "{reasoning_summary}" (if present)
│  → Tool calls: {tool_name}({args_summary})
│
├─ Phase 3: Tool Execution ({duration})
│  ⚙ {tool_name} → {output_summary}
│  ...
│
├─ ... (repeat for each LLM↔Tool loop)
│
└─ Final Response
   "{first 200 chars of output}"

### Token Summary
| Call | Input | Cached | Output | Reasoning |
|------|-------|--------|--------|-----------|
| #1   | ...   | ...    | ...    | ...       |
| Total| ...   | ...    | ...    | ...       |
```

**Span type details for analysis:**

- **`agent`**: Top-level agent span. `span_data.name` = agent name, `span_data.tools` = available tools list, `span_data.usage` = aggregated usage across all child response spans.
- **`response`**: An LLM call. Contains `span_data.model`, `span_data.usage` (input/output/cached/reasoning tokens), `span_data.tool_calls` (what the LLM decided to call), `span_data.reasoning` (chain-of-thought summary), `span_data.input` (last message that triggered this call), `span_data.output` (text output if final response).
- **`function`**: A tool execution. `span_data.name` = tool name, `span_data.input` = arguments JSON, `span_data.output` = result, `span_data.mcp_data.server` = which MCP server handled it.
- **`mcp_tools`**: MCP tool listing/discovery. `span_data.server` = server name, `span_data.result` = list of available tool names.

**Highlight interesting patterns:**
- Self-corrections (LLM reasoning that says it made a mistake and is retrying)
- Parallel tool calls (multiple tool_calls in one response span)
- Cache hit ratios (cached_tokens / input_tokens)
- Total execution time vs LLM thinking time vs tool execution time
