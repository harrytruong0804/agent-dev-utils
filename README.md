# agent-dev-utils

A Claude Code plugin marketplace with developer utilities for AI agent projects.

## Install

```bash
# Install a specific plugin from this marketplace
/install-plugin harrytruong0804/agent-dev-utils@openai-agents-tracing
/install-plugin harrytruong0804/agent-dev-utils@context-engineering-pro-max
```

## Plugins

### openai-agents-tracing

Self-hosted tracing dashboard for OpenAI Agent SDK — view traces, spans, token usage (cached/reasoning), and agent-level aggregation.

| Command | Description |
|---------|-------------|
| `/openai-agents-tracing:integrate` | Integrate tracing dashboard into the current project |
| `/openai-agents-tracing:remove` | Remove tracing dashboard from the current project |

**Docker images:** [`noitq/oat-api`](https://hub.docker.com/r/noitq/oat-api) / [`noitq/oat-client`](https://hub.docker.com/r/noitq/oat-client)

### context-engineering-pro-max

Context engineering audit for AI agent codebases — reviews system prompts, tool schemas, handoffs, guardrails, memory management, and orchestration logic. Produces a structured report with actionable feedback.

| Command | Description |
|---------|-------------|
| `/context-engineering-pro-max:context-engineering-reviewer` | Run a full context engineering audit on the current project |

**Supports:** OpenAI Agents SDK, LangGraph, CrewAI, and custom frameworks.

## Repo Structure

```
agent-dev-utils/
├── .claude-plugin/
│   └── marketplace.json
├── plugins/
│   ├── openai-agents-tracing/
│   │   ├── .claude-plugin/plugin.json
│   │   └── skills/
│   │       ├── integrate/
│   │       └── remove/
│   └── context-engineering-pro-max/
│       ├── .claude-plugin/plugin.json
│       └── skills/
│           └── context-engineering-reviewer/
│               ├── SKILL.md
│               └── references/
└── README.md
```

## License

MIT
