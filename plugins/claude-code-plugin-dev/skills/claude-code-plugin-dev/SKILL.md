---
name: claude-code-plugin-dev
description: >
  Guide for developing, versioning, releasing, and self-updating Claude Code plugins distributed
  via GitHub/Bitbucket marketplace repos. Use this skill whenever: the user is working on a Claude
  Code plugin codebase, asks about plugin release workflow, wants to bump a plugin version and push
  a new release, needs to update the currently-installed copy of a plugin they are developing,
  mentions "plugin version", "plugin release", "plugin update", "reload plugin", "self-update plugin",
  or refers to plugin.json versioning. Also trigger when the user says things like "ship it",
  "release a new version", "push plugin changes", or "update my installed plugin". This skill
  covers the full dev→test→version→commit→push→reinstall cycle for Claude Code plugins.
---

# Claude Code Plugin Development & Release Workflow

This skill guides the full lifecycle of developing a Claude Code plugin that is distributed
via a Git-based marketplace (GitHub, Bitbucket, or any Git host).

## Prerequisites

Before using this workflow, confirm:

1. The plugin repo exists and has a valid structure (`.claude-plugin/plugin.json` at minimum)
2. The repo is configured as a marketplace (has `.claude-plugin/marketplace.json`) OR the user
   installs via direct Git URL
3. The user has push access to the remote repository

If any of these are missing, help the user set them up first. Refer to
`references/plugin-structure.md` for the canonical directory layout.

---

## Workflow: Develop → Release → Self-Update

### Phase 1: Make Changes

1. **Identify what to change** — skills, commands, agents, hooks, MCP servers, or scripts
2. **Edit files** in the plugin working directory
3. **Test locally** before committing:

```bash
# Run Claude Code with the plugin loaded from the local directory
claude --plugin-dir ./your-plugin-name
```

Inside the session, use `/reload-plugins` after making further edits to pick up changes
without restarting Claude Code.

4. **Verify** the changes work as expected — test slash commands, skill triggering, hooks, etc.

### Phase 2: Version Bump

Update the version in `.claude-plugin/plugin.json`:

```json
{
  "name": "your-plugin",
  "version": "X.Y.Z",  // ← bump this
  "description": "..."
}
```

**Versioning convention** (semver):
- **PATCH** (`0.1.0 → 0.1.1`): Bug fixes, typo corrections, minor doc updates
- **MINOR** (`0.1.1 → 0.2.0`): New features, new commands/skills/agents, non-breaking changes
- **MAJOR** (`0.2.0 → 1.0.0`): Breaking changes, renamed commands, restructured config

Also update the version in `.claude-plugin/marketplace.json` if it exists (the `plugins[].version`
field should match `plugin.json`).

**Important**: When editing version numbers, update ALL locations where the version appears:
- `.claude-plugin/plugin.json` → `"version"` field
- `.claude-plugin/marketplace.json` → `plugins[].version` field (if present)
- `README.md` → version badges or changelog section (if present)
- `CHANGELOG.md` → add entry for the new version (if present)

### Phase 3: Commit & Push

```bash
# Stage all changes
git add -A

# Commit with a conventional message
git commit -m "feat: <description>" # or fix:, chore:, docs:, etc.

# Push to remote
git push origin main  # or master, or your default branch
```

**Commit message conventions:**
- `feat: add new /analyze command` — new feature (→ minor bump)
- `fix: correct skill trigger description` — bug fix (→ patch bump)
- `chore: update dependencies` — maintenance (→ patch bump)
- `docs: improve README examples` — documentation only
- `breaking: rename /old-cmd to /new-cmd` — breaking change (→ major bump)

### Phase 4: Update the Installed Plugin (Self-Update)

After pushing, the currently running Claude Code session still has the OLD cached version.
To update:

**Method A: Marketplace update + reinstall (recommended)**

```bash
# Step 1: Update the marketplace to fetch latest from remote
# Use /plugin command inside Claude Code:
/plugin marketplace update

# Step 2: Uninstall the old version
claude plugin uninstall your-plugin-name

# Step 3: Reinstall to get the new version
claude plugin install your-plugin-name@your-marketplace-name

# Step 4: Reload plugins in the current session
/reload-plugins
```

**Method B: Quick update via CLI (if the marketplace has auto-update enabled)**

```bash
# Update marketplace data
claude plugin marketplace update <marketplace-name>

# The plugin should auto-update if auto-update is enabled
# Then reload in session:
/reload-plugins
```

**Method C: Nuclear option — clear cache and reinstall**

```bash
# Remove the plugin cache
rm -rf ~/.claude/plugins/cache/<marketplace-name>/<plugin-name>/

# Update marketplace
claude plugin marketplace update <marketplace-name>

# Reinstall
claude plugin install <plugin-name>@<marketplace-name>

# Reload
/reload-plugins
```

**Method D: For development — just use --plugin-dir**

If you're actively developing and don't need the marketplace flow yet:

```bash
# This always loads the latest local code, no caching
claude --plugin-dir /path/to/your/plugin
```

---

## Quick Reference: Common Plugin CLI Commands

| Action | Command |
|--------|---------|
| Test plugin locally | `claude --plugin-dir ./my-plugin` |
| Reload after edits | `/reload-plugins` (inside session) |
| Add marketplace | `claude plugin marketplace add owner/repo` |
| List marketplaces | `claude plugin marketplace list` |
| Update marketplace | `claude plugin marketplace update <name>` |
| Install plugin | `claude plugin install <plugin>@<marketplace>` |
| Uninstall plugin | `claude plugin uninstall <plugin>` |
| Enable/disable | `claude plugin enable/disable <plugin>` |
| List installed | `claude plugin list` |

---

## Troubleshooting

**Plugin skills not appearing after update:**
```bash
rm -rf ~/.claude/plugins/cache
# Then reinstall
```

**"Permission denied" on plugin scripts (macOS/Linux):**
```bash
chmod +x your-plugin/scripts/*.sh
git add -A && git commit -m "fix: make scripts executable" && git push
```

**Installed version doesn't match latest commit:**
Plugins are pinned to the commit SHA at install time. You MUST update the marketplace
and reinstall to get newer commits. `/plugin marketplace update` alone only refreshes
the catalog — it does NOT update already-installed plugins unless auto-update is enabled.

**Changes to hooks not taking effect:**
Hooks from uninstalled plugins can persist until the next session. After reinstalling,
start a new Claude Code session to ensure clean hook state.

---

## One-Liner Release Script

For quick releases, you can add this as a script in your plugin repo:

```bash
#!/bin/bash
# scripts/release.sh — Usage: ./scripts/release.sh "0.2.0" "feat: add new analysis command"

VERSION=$1
MESSAGE=$2

if [ -z "$VERSION" ] || [ -z "$MESSAGE" ]; then
  echo "Usage: ./scripts/release.sh <version> <commit-message>"
  exit 1
fi

# Update plugin.json version
jq --arg v "$VERSION" '.version = $v' .claude-plugin/plugin.json > tmp.json && mv tmp.json .claude-plugin/plugin.json

# Update marketplace.json version if it exists
if [ -f ".claude-plugin/marketplace.json" ]; then
  jq --arg v "$VERSION" '.plugins[0].version = $v' .claude-plugin/marketplace.json > tmp.json && mv tmp.json .claude-plugin/marketplace.json
fi

# Commit and push
git add -A
git commit -m "$MESSAGE"
git tag "v$VERSION"
git push origin main --tags

echo "✅ Released v$VERSION"
echo "Run inside Claude Code to update:"
echo "  /plugin marketplace update"
echo "  Then reinstall or /reload-plugins"
```

Make it executable: `chmod +x scripts/release.sh`
