---
id: US-073
epic: EPIC-011
type: story
status: backlog
created: 2026-07-20
points: 5
tags: [hyperliquid, testnet, orders]
depends-on: US-072
---

# US-073: Testnet Market Data + Order Placement

## Story
As the execution system, I need to place entry orders on Hyperliquid testnet for BTC/ETH/SOL, so that paper trading signals can become real testnet positions.

## Acceptance Criteria
- [ ] Module `scripts/execution/hyperliquid_client.py` wrapping `hyperliquid-python-sdk`
- [ ] Function `place_entry_order(symbol, direction, size, order_type="limit")` — places entry only, no SL/TP yet (see US-074)
- [ ] Function `get_market_data(symbol)` — current price, for comparing against expected entry
- [ ] Hard safety check: refuses to run if `HYPERLIQUID_API_URL` is not the testnet URL (`api.hyperliquid-testnet.xyz`) — prevents accidental mainnet order placement
- [ ] Smoke test: place a small testnet order, confirm fill via account state query

## Definition of Done
- Can place and confirm a testnet order end-to-end
- Mainnet safety check verified (test that it refuses to run against a mainnet-looking URL)
- Committed to main
