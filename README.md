# agent-dev-utils

Claude Code plugin with developer utilities for OpenAI Agent SDK projects.

## Install

```bash
/install-plugin harrytruong0804/agent-dev-utils
```

## Skills

### OAT (OpenAI Agents Tracing)

Self-hosted tracing dashboard for OpenAI Agent SDK — view traces, spans, token usage (cached/reasoning), and agent-level aggregation.

| Command | Description |
|---------|-------------|
| `/agent-dev-utils:oat` | Integrate OAT into the current project |
| `/agent-dev-utils:oat-remove` | Remove OAT integration from the current project |

**`/oat` generates:**
- `docker-compose.oat.yml` — MongoDB + OAT API + OAT Client
- `oat_tracing_processor.py` — TracingProcessor with rich span extraction, cached/reasoning token tracking, agent-level usage aggregation
- Config entries — `oat_dashboard_enabled`, `oat_dashboard_api_url`, `oat_dashboard_api_key`
- Integration wiring — hooks the processor into `set_trace_processors()`

**`/oat-remove`** cleanly undoes everything `/oat` created.

**Docker images:** [`noitq/oat-api`](https://hub.docker.com/r/noitq/oat-api) / [`noitq/oat-client`](https://hub.docker.com/r/noitq/oat-client)

## Adding more skills

This repo is designed to hold multiple utility skill sets. To add a new one:

```
skills/
├── oat/            # /agent-dev-utils:oat
├── oat-remove/     # /agent-dev-utils:oat-remove
├── new-tool/       # /agent-dev-utils:new-tool
└── new-tool-remove/
```

## License

MIT
