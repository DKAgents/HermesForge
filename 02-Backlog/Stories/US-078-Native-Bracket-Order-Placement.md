---
id: US-078
epic: EPIC-012
type: story
status: backlog
created: 2026-07-20
points: 3
tags: [alpaca, bracket-orders]
depends-on: US-077
---

# US-078: Native Bracket Order Placement

## Story
As the execution system, I need to place native Alpaca bracket orders (entry+SL+TP as one linked OCO group), so that stock paper trades are protected without the manual leg-management complexity Hyperliquid requires.

## Acceptance Criteria
- [ ] Function `place_bracket_order(symbol, direction, qty, entry_price, stop_price, target_price)` in `alpaca_client.py`
- [ ] Confirms order acceptance and links entry/SL/TP as a single bracket group via Alpaca's native support
- [ ] Smoke test: place a bracket order in paper mode, confirm all three legs are visible and linked in the account

## Definition of Done
- Bracket order smoke test passes against Alpaca paper API
- Committed to main
