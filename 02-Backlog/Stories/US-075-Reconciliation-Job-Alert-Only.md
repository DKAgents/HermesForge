---
id: US-075
epic: EPIC-011
type: story
status: backlog
created: 2026-07-20
points: 3
tags: [hyperliquid, reconciliation, alert-only, risk]
depends-on: US-074
---

# US-075: Reconciliation Job (Alert-Only)

## Story
As the risk-conscious system operator, I need a job that detects dangling single-leg positions (entry filled, SL/TP missing) and alerts me, without taking any automatic closing action, so that I always have final control over exiting a testnet position.

## Acceptance Criteria
- [ ] Script `scripts/execution/reconcile_hyperliquid.py` runs on startup and periodically (recommend hourly during market-relevant hours)
- [ ] Compares live testnet account positions against the persisted local state (US-074) — flags any position where entry is filled but SL and/or TP is missing/unconfirmed
- [ ] On detecting a dangling position: sends a Discord alert with position details (symbol, side, size, entry price, time since entry) — **does not place, cancel, or modify any order automatically**
- [ ] This is a deliberate, user-approved design choice (2026-07-20) — even on testnet, no auto-close-to-flat behavior. Document this explicitly in the script's docstring so a future contributor doesn't "fix" it into auto-closing.

## Definition of Done
- Reconciliation job detects a manually-created dangling position in a test scenario and alerts correctly
- Confirmed it takes no closing action in that test
- Committed to main
