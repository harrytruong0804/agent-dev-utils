# agent-dev-utils

Claude Code plugin for OpenAI Agent SDK projects. Provides slash commands for setting up and managing the [OAT (OpenAI Agents Tracing)](https://github.com/yusuf-eren/openai-agents-tracing) dashboard.

## Skills

| Command | Description |
|---------|-------------|
| `/agent-dev-utils:setup-oat` | Set up OAT in your project — generates docker-compose, tracing processor, config, and integration code |
| `/agent-dev-utils:update-oat [version]` | Pull latest OAT Docker images and restart the dashboard |

## Install

```bash
# In Claude Code
/install-plugin harrytruong0804/agent-dev-utils
```

## What `/setup-oat` generates

- **`docker-compose.oat.yml`** — MongoDB + OAT API + OAT Client, ready to `docker compose up`
- **`oat_tracing_processor.py`** — `TracingProcessor` implementation that exports spans to the OAT dashboard, with:
  - Rich span data extraction (model, usage, reasoning, tool calls)
  - Cached & reasoning token tracking (`input_tokens_details`, `output_tokens_details`)
  - Agent-level usage aggregation (rolls up child span tokens)
- **Config entries** — Pydantic settings for `oat_dashboard_enabled`, `oat_dashboard_api_url`, `oat_dashboard_api_key`
- **Integration snippet** — Wires the processor into `set_trace_processors()`

## OAT Docker Images

Images on Docker Hub:
- [`noitq/oat-api`](https://hub.docker.com/r/noitq/oat-api)
- [`noitq/oat-client`](https://hub.docker.com/r/noitq/oat-client)

## Quick Start

```bash
# 1. Run setup-oat in your project
/agent-dev-utils:setup-oat

# 2. Start the dashboard
docker compose -f docker-compose.oat.yml up -d

# 3. Enable in .env
OAT_DASHBOARD_ENABLED=true

# 4. Open dashboard
# http://localhost:3800
```

## License

MIT
