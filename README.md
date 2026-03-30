# agent-dev-utils

A Claude Code plugin marketplace with developer utilities for OpenAI Agent SDK projects.

## Install

```bash
# Install a specific plugin from this marketplace
/install-plugin harrytruong0804/agent-dev-utils@oat
```

## Plugins

### OAT (OpenAI Agents Tracing)

Self-hosted tracing dashboard for OpenAI Agent SDK — view traces, spans, token usage (cached/reasoning), and agent-level aggregation.

| Command | Description |
|---------|-------------|
| `/oat:integrate` | Integrate OAT into the current project |
| `/oat:remove` | Remove OAT integration from the current project |

**`/oat:integrate` generates:**
- `docker-compose.oat.yml` — MongoDB + OAT API + OAT Client
- `oat_tracing_processor.py` — TracingProcessor with rich span extraction, cached/reasoning token tracking, agent-level usage aggregation
- Config entries — `oat_dashboard_enabled`, `oat_dashboard_api_url`, `oat_dashboard_api_key`
- Integration wiring — hooks the processor into `set_trace_processors()`

**`/oat:remove`** cleanly undoes everything `/oat:integrate` created.

**Docker images:** [`noitq/oat-api`](https://hub.docker.com/r/noitq/oat-api) / [`noitq/oat-client`](https://hub.docker.com/r/noitq/oat-client)

## Repo Structure

```
agent-dev-utils/
├── .claude-plugin/
│   └── marketplace.json           # marketplace catalog
├── plugins/
│   ├── oat/                       # OAT plugin
│   │   ├── .claude-plugin/
│   │   │   └── plugin.json
│   │   └── skills/
│   │       ├── integrate/
│   │       │   ├── SKILL.md
│   │       │   └── templates/
│   │       └── remove/
│   │           └── SKILL.md
│   └── <future-plugin>/           # add more plugins here
└── README.md
```

## License

MIT
