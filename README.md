# agent-dev-utils

A Claude Code plugin marketplace with developer utilities for OpenAI Agent SDK projects.

## Install

```bash
# Install a specific plugin from this marketplace
/install-plugin harrytruong0804/agent-dev-utils@openai-agents-tracing
```

## Plugins

### openai-agents-tracing

Self-hosted tracing dashboard for OpenAI Agent SDK — view traces, spans, token usage (cached/reasoning), and agent-level aggregation.

| Command | Description |
|---------|-------------|
| `/openai-agents-tracing:integrate` | Integrate tracing dashboard into the current project |
| `/openai-agents-tracing:remove` | Remove tracing dashboard from the current project |

**`/openai-agents-tracing:integrate` generates:**
- `docker-compose.oat.yml` — MongoDB + API + Client dashboard
- `oat_tracing_processor.py` — TracingProcessor with rich span extraction, cached/reasoning token tracking, agent-level usage aggregation
- Config entries — `oat_dashboard_enabled`, `oat_dashboard_api_url`, `oat_dashboard_api_key`
- Integration wiring — hooks the processor into `set_trace_processors()`

**`/openai-agents-tracing:remove`** cleanly undoes everything.

**Docker images:** [`noitq/oat-api`](https://hub.docker.com/r/noitq/oat-api) / [`noitq/oat-client`](https://hub.docker.com/r/noitq/oat-client)

## Repo Structure

```
agent-dev-utils/
├── .claude-plugin/
│   └── marketplace.json
├── plugins/
│   ├── openai-agents-tracing/
│   │   ├── .claude-plugin/
│   │   │   └── plugin.json
│   │   └── skills/
│   │       ├── integrate/
│   │       │   ├── SKILL.md
│   │       │   └── templates/
│   │       └── remove/
│   │           └── SKILL.md
│   └── <future-plugin>/
└── README.md
```

## License

MIT
