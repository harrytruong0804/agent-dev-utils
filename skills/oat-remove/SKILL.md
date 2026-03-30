---
name: oat-remove
description: Remove OAT (OpenAI Agents Tracing) integration from the current project. Deletes generated files, config entries, and wiring code.
---

# Remove OAT Integration

Cleanly remove all OAT tracing dashboard files and configuration from this project.

## Steps

### 1. Stop running containers (if any)

```bash
docker compose -f docker-compose.oat.yml down 2>/dev/null || true
```

### 2. Delete generated files

- Delete `docker-compose.oat.yml` from project root
- Find and delete `oat_tracing_processor.py` (search in services directories)

### 3. Remove config entries

Find the project's settings/config file and remove these fields:
- `oat_dashboard_enabled`
- `oat_dashboard_api_url`
- `oat_dashboard_api_key`

Also remove any related validator methods for these fields.

### 4. Remove `.env.example` entries

Remove the OAT section:
```
# OAT Dashboard (OpenAI Agents Tracing)
OAT_DASHBOARD_ENABLED=false
OAT_DASHBOARD_API_URL=http://localhost:3801
OAT_DASHBOARD_API_KEY=
```

### 5. Remove integration wiring

Find and remove the OAT initialization block. It typically looks like:

```python
if settings.oat_dashboard_enabled:
    ...set_trace_processors...
    ...OpenAIAgentsTracingDashboardProcessor...
```

Remove the entire conditional block and its imports.

### 6. Remove `.env` entries (if present)

Remove from `.env`:
```
OAT_DASHBOARD_ENABLED=...
OAT_DASHBOARD_API_URL=...
OAT_DASHBOARD_API_KEY=...
```

## After removal

Print a summary:

```
OAT removed successfully!

Files deleted:
  - docker-compose.oat.yml
  - <path>/oat_tracing_processor.py

Files modified:
  - <config_file> (removed oat_dashboard_* settings)
  - .env.example (removed OAT env vars)
  - <tracing_init_file> (removed OAT processor wiring)

Note: Docker volumes (oat_mongodb_data) were NOT removed.
To also remove data: docker volume rm oat_mongodb_data
```
