---
id: US-119
type: user-story
epic: EPIC-009
status: in-progress
priority: high
effort: L
created: 2026-08-17
updated: 2026-08-18
assigned_to: agent
tags: [backlog, story, crypto, liquidation, monitoring, webhook, mcp, real-time]
---

# US-119: Real-Time Market Event Monitoring (Liquidation/Funding/OI)

## Story
**As a** trading system operator,
**I want** real-time monitoring of liquidation cascades, funding rate extremes, and OI spikes with event-driven alerts,
**So that** confidence scores on pending signals can be adjusted based on market stress events.

## Context
Built as part of the Hermes v0.20.3 update integration. Combines:
- Webhook event triggers (new Hermes feature)
- MCP server for trading data (new Hermes feature)
- Free data from Hyperliquid (no paid APIs)
- Proxy detection for liquidations (Hyperliquid REST doesn't expose liquidation events — WebSocket only)

## Acceptance Criteria
- [x] Cron-based monitoring scripts: check_liquidations.py, check_funding_extremes.py, check_oi_spikes.py
- [x] Liquidation cascade proxy: OI drop >5% + price move >1.5% in same window
- [x] Funding rate extreme detection with absolute thresholds
- [x] OI spike detection (>5% change between snapshots)
- [x] Real-time listener daemon (liquidation_listener.py) for systemd
- [x] systemd service configured (hermesforge-listener.service)
- [x] Event logging to JSONL for historical analysis
- [x] Hermes webhook platform enabled (port 8644)
- [x] MCP server with 6 tools (fetch_oi, fetch_funding_rate, fetch_orderbook, fetch_regime, get_open_trades, fetch_all_oi)
- [x] Cron recipes for 4 monitoring patterns
- [ ] Register MCP server with Hermes (after gateway restart)
- [ ] Start listener service (after webhook verification)
- [ ] Walk-forward validation of confidence adjustment logic

## Implementation
### Files Created
- `scripts/monitoring/check_liquidations.py` — cron liquidation cascade proxy
- `scripts/monitoring/check_funding_extremes.py` — cron funding rate monitor
- `scripts/monitoring/check_oi_spikes.py` — cron OI spike monitor
- `scripts/monitoring/liquidation_listener.py` — real-time daemon
- `scripts/monitoring/cron_recipes.py` — reusable monitoring templates
- `scripts/monitoring/hermesforge_mcp_server.py` — MCP server (6 tools)
- `/etc/systemd/system/hermesforge-listener.service` — systemd service

### Architecture
```
Hyperliquid API → liquidation_listener.py (every 10s)
                    ├── Liquidation proxy (OI drop + price move)
                    ├── Funding extremes (every 5 min)
                    └── OI spikes (every 15 min)
                         │
                         ├── Log to JSONL
                         └── Fire webhook → Hermes agent run
                                               ├── Analyze event
                                               ├── Check open trades
                                               ├── Post alert to Discord
                                               └── Adjust confidence scores

MCP Server (stdio) → Hermes MCP client
                       ├── fetch_oi(coin)
                       ├── fetch_funding_rate(coin)
                       ├── fetch_orderbook(coin, depth)
                       ├── fetch_regime()
                       ├── get_open_trades()
                       └── fetch_all_oi()
```

## Limitations
- Liquidation detection is a PROXY (OI drop + price move), not actual liquidation events
- Hyperliquid liquidation data is WebSocket-only, not REST
- Listener starts in --dry-run mode for safety
- Webhook not yet active (requires gateway restart to v0.20.3)
- MCP server not yet registered with Hermes (requires `hermes mcp add`)
