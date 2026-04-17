---
name: hermes-ops
description: >
  CONSULT THIS SKILL before attempting any hermes-agent operation — it contains critical
  deployment gotchas that Claude does not know by default and will get wrong without it.
  Required for: hermes tenant management (add-tenant.sh, remove-tenant.sh, hermesctl up/down/
  logs/ps/ls/doctor), running hermes doctor or any command inside a hermes container (docker
  exec requires --user hermes and /opt/hermes/.venv/bin/hermes — NOT just "hermes"), approving
  a hermes bot pairing code via hermesctl approve (NOT the telegram:access skill — that is for
  Claude Code's own Telegram; this skill handles hermes bot platform pairing), Weixin/WeChat
  QR-login pairing (weixin-pair.sh), reloading .env changes without data loss (must use
  force-recreate, not restart), and deleting UID-10000 owned data directories. Trigger on:
  hermes tenant, hermes container, hermes gateway, hermesctl, hermes doctor, hermes pairing
  code, weixin-pair, add-tenant, or any deploy/ directory operation.
---

# Hermes-Agent Instance Operations

All operations run from the `deploy/` directory. The central tool is `./hermesctl` — a thin
wrapper that auto-discovers all `tenants/*/compose.yml` fragments and passes them to
`docker compose`. Always use `./hermesctl` instead of bare `docker compose`; bare compose
only sees the base file and has no services.

---

## Bundled Scripts

This skill includes a **complete, self-contained copy** of the `deploy/` directory. You do
not need to clone the hermes-agent repo to operate a hermes instance.

```bash
# Bootstrap a fresh deployment from the bundled scripts:
SKILL_DIR=~/.claude/skills/hermes-ops
mkdir -p ~/hermes-deploy
cp -r "$SKILL_DIR/deploy/." ~/hermes-deploy/
chmod +x ~/hermes-deploy/hermesctl \
         ~/hermes-deploy/add-tenant.sh \
         ~/hermes-deploy/remove-tenant.sh \
         ~/hermes-deploy/scripts/*.sh
cd ~/hermes-deploy
```

Then proceed with the normal setup below. The bundled `tenants/` directory contains example
tenant compose fragments (`poc`, `alice`, `bob`) — copy and rename as needed.

---

## Quick Reference

```bash
cd ~/hermes-deploy/          # or wherever you copied the bundled scripts

# Status
./hermesctl ls                               # tenants + container status + active platforms
./hermesctl ps                               # docker-level container table
./hermesctl doctor                           # validate config (ports, keys, UID, orphans)

# Lifecycle
./hermesctl up -d                            # start all tenants
./hermesctl up -d <tenant>                   # start one tenant
./hermesctl up -d --force-recreate <tenant>  # reload .env changes — use this, not restart
./hermesctl down                             # stop all
./hermesctl logs -f <tenant>                 # tail logs (containers use `gateway run -v`)
./hermesctl logs --tail 200 <tenant>         # last 200 lines

# Debug
./hermesctl config                           # merged compose (great for path/env debugging)
docker exec --user hermes hermes-<tenant> /opt/hermes/.venv/bin/hermes doctor
docker exec --user hermes hermes-<tenant> /opt/hermes/.venv/bin/hermes <cmd>
```

---

## Tenant Lifecycle

### First-time setup

```bash
cd deploy/
cp .env.shared.example .env.shared
$EDITOR .env.shared    # fill in LLM API keys (e.g. ANTHROPIC_API_KEY)
```

### Add a tenant

```bash
./add-tenant.sh <name>           # scaffold tenants/<name>/{compose.yml, .env, data/}
$EDITOR tenants/<name>/.env      # add bot tokens for each platform
./hermesctl up -d <name>
./hermesctl logs -f <name>       # verify clean startup
```

Tenant names must match `[a-z0-9][a-z0-9-]+` (lowercase, digits, hyphens).

### Update config after editing .env

`docker restart` and `hermesctl restart` keep the old container environment — they do **not**
reload `env_file`. The only way to pick up `.env` changes is:

```bash
./hermesctl up -d --force-recreate <tenant>
```

### Remove a tenant

```bash
# Default: stop container + archive data (safe, reversible)
./remove-tenant.sh <name>
# → moved to tenants/.archive/<name>-<timestamp>/

# Permanent delete (prompts for name confirmation)
./remove-tenant.sh <name> --purge
```

The `data/` directory is owned by UID 10000 (the container's `hermes` user), so a plain
host-side `rm -rf` will fail. To wipe archived data:

```bash
docker run --rm \
  -v "$(pwd)/tenants/.archive/<name>-<ts>:/w" \
  alpine sh -c 'rm -rf /w/data'
rm -rf tenants/.archive/<name>-<ts>
```

---

## Platform Pairing

### WeChat / Weixin

```bash
# Container must already be running
./scripts/weixin-pair.sh -t <tenant> --restart
```

What it does:
1. Runs the QR login flow inside the container — a QR code appears in the terminal
2. Scan it in WeChat within ~8 minutes
3. On success: writes `WEIXIN_ACCOUNT_ID`, `WEIXIN_TOKEN`, `WEIXIN_BASE_URL` to `tenants/<tenant>/.env`
4. `--restart` force-recreates the container and waits up to 120 s for `[weixin] Connected account=` in logs

If you omit `--restart`, reload manually:
```bash
./hermesctl up -d --force-recreate <tenant>
```

### Telegram

The pairing code appears in the container logs when a user messages the bot. Approve it:

```bash
./hermesctl approve -t <tenant> -p telegram -c <code>
# e.g.: ./hermesctl approve -t poc -p telegram -c 85TC3GMF
```

### Other platforms (Discord, Slack, Signal, Matrix…)

Set the relevant token(s) in `tenants/<tenant>/.env`, then force-recreate to apply.
Run `./hermesctl ls` afterwards — the platforms column confirms what's active.

---

## docker exec Rules

Two rules that prevent silent failures:

**1. Always pass `--user hermes`**
The default user in `docker exec` is root. Running as root creates root-owned files inside
`/opt/data/`, which then block writes from the container's UID-10000 `hermes` user.

**2. Always use the full venv path**
`exec` bypasses the entrypoint venv activation, so `hermes` is not on PATH:

```bash
# Correct
docker exec --user hermes hermes-<tenant> /opt/hermes/.venv/bin/hermes <cmd>

# Wrong — "hermes: not found"
docker exec hermes-<tenant> hermes <cmd>
```

---

## Common Issues

| Symptom | Cause | Fix |
|---------|-------|-----|
| `.env` change has no effect after restart | `restart` doesn't reload `env_file` | `hermesctl up -d --force-recreate <tenant>` |
| `rm -rf tenants/<name>/data` → Permission denied | UID 10000 ownership | Delete via alpine container (see "Remove a tenant") |
| `hermes: command not found` in exec | venv not activated | Use `/opt/hermes/.venv/bin/hermes` |
| INFO logs ("Connected to Telegram", "Gateway running") not visible | Default log verbosity filters them | Containers use `gateway run -v`; check logs again |
| Container exits immediately | Bad/missing env var | `./hermesctl logs --tail 100 <tenant>` |
| Port conflict between tenants | Shared `API_SERVER_PORT` | Run `./hermesctl doctor`; assign unique ports in each tenant's `.env` |
| `./hermesctl config` shows no services | Running bare `docker compose` instead | Always use `./hermesctl`, never bare `docker compose` |

---

## Credential Loading Order

Later values win on conflict:

1. `.env.shared` — LLM keys, shared tool config, terminal defaults
2. `tenants/<name>/.env` — bot tokens, platform config, optional per-tenant key overrides

To make any key tenant-specific, move it from `.env.shared` to the tenant's `.env`.
