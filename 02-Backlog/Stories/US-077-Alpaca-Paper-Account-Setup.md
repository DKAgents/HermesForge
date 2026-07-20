---
id: US-077
epic: EPIC-012
type: story
status: backlog
created: 2026-07-20
points: 2
tags: [alpaca, paper-trading, setup]
---

# US-077: Alpaca Paper Account + API Key Wiring

## Story
As the execution system, I need an authenticated connection to Alpaca's paper trading API, so that stock signals can be placed as paper orders.

## Acceptance Criteria
- [ ] Alpaca paper trading account created (free at alpaca.markets)
- [ ] API key + secret stored in `~/.hermes/.env` (never committed)
- [ ] Module `scripts/execution/alpaca_client.py` wrapping the Alpaca API (via `alpaca-py` or REST)
- [ ] Connection test: query account state, confirm paper trading mode (not live) is active
- [ ] Hard safety check: refuses to run if the account/base URL resolves to a live trading endpoint

## Definition of Done
- Alpaca paper connection verified
- Live-endpoint safety check tested
- Committed to main
