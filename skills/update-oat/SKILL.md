---
name: update-oat
description: Update OAT dashboard Docker images to a specific version and restart containers
argument-hint: "[version]"
---

# Update OAT Dashboard

Pull the latest (or specified version) OAT Docker images and restart the dashboard.

## Arguments

- `$ARGUMENTS` — version tag (e.g., `1.0.0`). Defaults to `latest` if omitted.

## Steps

1. Determine the version: use `$ARGUMENTS` if provided, otherwise `latest`
2. Find `docker-compose.oat.yml` in the project root
3. Pull new images:
   ```bash
   docker pull noitq/oat-api:<version>
   docker pull noitq/oat-client:<version>
   ```
4. Restart with the new version:
   ```bash
   OAT_VERSION=<version> docker compose -f docker-compose.oat.yml up -d
   ```
5. Verify containers are running:
   ```bash
   docker compose -f docker-compose.oat.yml ps
   ```

## Output

Print the running container status and the dashboard URL:
```
OAT updated to <version>
Dashboard: http://localhost:3800
API:       http://localhost:3801
```
