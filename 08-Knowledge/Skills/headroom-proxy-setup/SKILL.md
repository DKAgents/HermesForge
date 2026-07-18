---
name: headroom-proxy-setup
description: "Set up, configure, and manage the Headroom AI token compression proxy on the HermesForge VPS. Covers install, systemd service, Hermes routing, and stats monitoring."
version: 1.1.0
author: HermesForge Orchestrator
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [headroom, proxy, token-compression, cost-optimization, openrouter, systemd]
    related_skills: [llm-proxy-integration]
---

# Skill: Headroom AI Proxy Setup

## When to Use
- Setting up the Headroom proxy on a fresh VPS
- Diagnosing why token compression isn't working
- Checking current savings stats
- Restarting the proxy after config changes

## Current VPS State
| Item | Value |
|---|---|
| Version | 0.28.0 |
| Port | 8787 |
| Backend | OpenRouter |
| Service | systemd (`headroom.service`) |
| Log file | `~/.hermes/logs/headroom.jsonl` |
| Hermes `base_url` | reverted to `provider: openrouter` (direct) |
| Stats endpoint | `http://127.0.0.1:8787/stats` |

---

## Installation

```bash
pip install "headroom-ai[proxy]"
headroom --version
headroom doctor
```

The binary installs inside the active venv:
```bash
which headroom
# /usr/local/lib/hermes-agent/venv/bin/headroom
```

---

## Systemd Service

Service file at `/etc/systemd/system/headroom.service`:
```ini
[Unit]
Description=Headroom AI Proxy
After=network.target

[Service]
Type=simple
User=root
EnvironmentFile=/root/.hermes/.env
ExecStart=/usr/local/lib/hermes-agent/venv/bin/headroom proxy \
  --port 8787 \
  --backend openrouter \
  --log-file /root/.hermes/logs/headroom.jsonl
Restart=on-failure
RestartSec=5
Environment=PATH=/usr/local/lib/hermes-agent/venv/bin:/usr/local/bin:/usr/bin:/bin
Environment=HOME=/root

[Install]
WantedBy=multi-user.target
```

### Service Management
```bash
systemctl status headroom      # check status
systemctl restart headroom     # restart
systemctl stop headroom        # stop
journalctl -u headroom -f      # tail logs
```

---

## Routing Hermes Through the Proxy

> ⚠️ **Critical:** `provider: openrouter` ignores `base_url` — it has a hardcoded URL.
> To route through Headroom, you must use `provider: custom`.

```bash
hermes config set model.provider custom
hermes config set model.base_url "http://127.0.0.1:8787/v1"
hermes config set model.api_key_env "OPENROUTER_API_KEY"
# Then /restart in Discord
```

To revert to direct OpenRouter (current state):
```bash
hermes config set model.provider openrouter
# Then /restart in Discord
```

---

## Health & Stats

```bash
curl http://127.0.0.1:8787/health         # proxy up/down
headroom doctor                            # full diagnostic
curl http://127.0.0.1:8787/stats          # full JSON stats
```

Key fields in `/stats`:
- `summary.api_requests` — total LLM calls through proxy
- `summary.compression.total_tokens_removed` — tokens saved this session
- `persistent_savings.lifetime.tokens_saved` — lifetime savings
- `persistent_savings.lifetime.requests` — lifetime request count

Stats are reset on service restart. Lifetime data persists in `~/.headroom/proxy_savings.json`.

---

## Daily Stats Cron Job

Job `ad0e12500771` (`Headroom Daily Savings Report [T3]`) runs daily at 08:00 UTC,
executes `~/headroom_stats.sh`, and delivers to `#headroom-stats` Discord channel.

---

## Pitfalls

| Problem | Fix |
|---|---|
| `headroom` command not found in systemd | Use full venv path: `/usr/local/lib/hermes-agent/venv/bin/headroom` |
| `api_requests` stays 0 after messages | Hermes is not routing through proxy — check `provider: custom` is set |
| EnvironmentFile missing | Systemd unit needs `EnvironmentFile=/root/.hermes/.env` for `OPENROUTER_API_KEY` |
| Stats show $0 savings | OpenRouter pricing not configured in Headroom — tokens are saved, cost calc needs pricing config |
| `headroom doctor` warnings for claude/codex | Expected — those CLI tools aren't installed; proxy still works |
| Stats reset after restart | Normal — lifetime data in `~/.headroom/proxy_savings.json` persists |
