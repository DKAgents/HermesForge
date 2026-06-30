---
id: SKILL-Headroom-Proxy-Setup
type: skill-doc
created: 2026-06-30
updated: 2026-06-30
status: active
tags: [skill, headroom, proxy, compression, optimization]
---

# Skill: Headroom AI Proxy Setup

## Overview
Headroom is a token compression + semantic caching proxy that sits between Hermes and the LLM provider. It reduces token usage and cost by compressing conversation history before sending to the API.

## Installation
```bash
pip install "headroom-ai[proxy]"
headroom --version
headroom doctor
```

## VPS Configuration
- **Version**: 0.28.0
- **Port**: 8787
- **Backend**: OpenRouter
- **Service**: systemd (`headroom.service`)
- **Log file**: `~/.hermes/logs/headroom.jsonl`
- **Hermes base_url**: `http://127.0.0.1:8787/v1`

## Service Management
```bash
systemctl status headroom      # check status
systemctl restart headroom     # restart
systemctl stop headroom        # stop
journalctl -u headroom -f      # tail logs
```

## Health Check
```bash
curl http://127.0.0.1:8787/health
headroom doctor
curl http://127.0.0.1:8787/stats    # token savings stats
```

## Systemd Unit Location
`/etc/systemd/system/headroom.service`

## Pitfalls
- Headroom binary is inside the Hermes venv: `/usr/local/lib/hermes-agent/venv/bin/headroom`
- EnvironmentFile must point to `~/.hermes/.env` so OPENROUTER_API_KEY is loaded
- After changes to `config.yaml`, restart the Hermes gateway (`/restart` in Discord)
- `headroom doctor` warnings for claude/codex are expected — those tools aren't installed

## Verification
```bash
headroom doctor          # proxy + version should show ✓ pass
curl http://127.0.0.1:8787/stats   # check savings after first requests
```
