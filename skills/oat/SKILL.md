---
name: oat
description: Integrate OAT (OpenAI Agents Tracing) dashboard into the current project. Generates docker-compose, tracing processor, config entries, and wiring code.
argument-hint: "[--force]"
---

# Integrate OAT (OpenAI Agents Tracing)

Add self-hosted tracing dashboard support to this OpenAI Agent SDK project.

## Arguments

- `--force`: Overwrite existing OAT files if they already exist

## Pre-checks

1. Verify this is a Python project using the OpenAI Agent SDK (`openai-agents` or `agents` in dependencies)
2. Check if OAT is already integrated (look for `oat_tracing_processor.py` or `oat_dashboard_enabled` in config). If found and `--force` not passed, inform the user and stop.
3. Identify the project's package structure:
   - Find the services/modules directory (e.g., `src/<package>/services/`)
   - Find the config/settings file (Pydantic Settings class)
   - Find where tracing is initialized (look for `set_trace_processors`, `set_tracing_disabled`, or agent setup)
   - Find the logger pattern used (e.g., `from myapp.logger import get_logger` or `import logging`)

## Files to generate

### 1. `docker-compose.oat.yml` (project root)

Copy the template at [templates/docker-compose.oat.yml](templates/docker-compose.oat.yml) to the project root.

### 2. Tracing Processor

Use the template at [templates/oat_tracing_processor.py](templates/oat_tracing_processor.py) as the base.

**Adapt before writing:**
- Replace the logger import to match the project's pattern
- Write to `<services_dir>/oat_tracing_processor.py`

### 3. Config entries

Add to the project's settings/config file (typically a Pydantic `Settings` class):

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

Append if not already present:

```
# OAT Dashboard (OpenAI Agents Tracing)
OAT_DASHBOARD_ENABLED=false
OAT_DASHBOARD_API_URL=http://localhost:3801
OAT_DASHBOARD_API_KEY=
```

### 5. Integration wiring

Find where tracing is initialized and add the OAT processor setup:

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

### 6. Dependency check

Verify `httpx` is in the project's dependencies. If not, inform the user to add it:
```
poetry add httpx   # or: pip install httpx
```

## After generation

Print a summary:

```
OAT integrated successfully!

Files created:
  - docker-compose.oat.yml
  - <path>/oat_tracing_processor.py

Files modified:
  - <config_file> (added oat_dashboard_* settings)
  - .env.example (added OAT env vars)
  - <tracing_init_file> (added OAT processor wiring)

To start:
  1. docker compose -f docker-compose.oat.yml up -d
  2. Set OAT_DASHBOARD_ENABLED=true in .env
  3. Dashboard: http://localhost:3800
```
