---
name: setup-oat
description: Set up OpenAI Agents Tracing (OAT) dashboard in the current project. Generates docker-compose, tracing processor, config entries, and integration code.
argument-hint: "[--force]"
---

# Setup OAT (OpenAI Agents Tracing)

Add self-hosted tracing dashboard support to this OpenAI Agent SDK project.

## Arguments

- `--force`: Overwrite existing OAT files if they already exist

## What to generate

Generate the following files. Read existing project files first to match the codebase's style, import patterns, and logger usage.

### 1. `docker-compose.oat.yml`

Use the template at [templates/docker-compose.oat.yml](templates/docker-compose.oat.yml). Write it to the project root.

### 2. Tracing Processor

Use the template at [templates/oat_tracing_processor.py](templates/oat_tracing_processor.py) as the base.

**Adapt before writing:**
- Find the project's services/modules directory (e.g., `src/<package>/services/`)
- Match the project's logger import pattern (e.g., `from myapp.logger import get_logger` or `import logging`)
- If the project uses a different logger, replace the `get_logger(__name__)` call accordingly
- Write to `<services_dir>/oat_tracing_processor.py`

### 3. Config entries

Find the project's settings/config file (typically a Pydantic `Settings` class). Add these fields if they don't already exist:

```python
# OpenAI Agents Tracing Dashboard
oat_dashboard_enabled: bool = Field(
    default=False,
    description="Enable export to self-hosted OAT dashboard",
)
oat_dashboard_api_url: str = Field(
    default="http://localhost:3801",
    description="OAT dashboard API base URL",
)
oat_dashboard_api_key: Optional[str] = Field(
    default=None,
    description="API key for OAT dashboard ingestion",
)
```

### 4. `.env.example` entries

Append these if not already present:

```
# OAT Dashboard (OpenAI Agents Tracing)
OAT_DASHBOARD_ENABLED=false
OAT_DASHBOARD_API_URL=http://localhost:3801
OAT_DASHBOARD_API_KEY=
```

### 5. Integration code

Find where the Agent SDK client or tracing is initialized (look for `set_trace_processors`, `set_tracing_disabled`, or agent/runner setup). Add OAT initialization:

```python
if settings.oat_dashboard_enabled:
    from agents import set_trace_processors
    from <package>.services.oat_tracing_processor import (
        OpenAIAgentsTracingDashboardProcessor,
    )
    processor = OpenAIAgentsTracingDashboardProcessor(
        api_url=settings.oat_dashboard_api_url,
        api_key=settings.oat_dashboard_api_key or "",
    )
    set_trace_processors([processor])
```

Adapt the import path to match the project structure.

## After generation

Print a summary of what was created and how to start:

```
OAT setup complete!

Files created:
  - docker-compose.oat.yml
  - <path>/oat_tracing_processor.py
  - Config entries added to <config_file>
  - .env.example updated

To start the dashboard:
  docker compose -f docker-compose.oat.yml up -d

Then set in .env:
  OAT_DASHBOARD_ENABLED=true

Dashboard UI: http://localhost:3800
```
