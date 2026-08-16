---
type: user-story
story: US-111
epic: EPIC-013
title: "Portfolio Risk Guard"
status: Done
created: 2026-08-15
completed: 2026-08-15
tags: [risk-management, portfolio, circuit-breaker]
---

# US-111: Portfolio Risk Guard

## Summary

Built and wired a pre-entry portfolio risk guard that protects against over-concentration, drawdown cascades, and excessive exposure. Replaces the previously suspended heat cap.

## Risk Controls Implemented

| Control | Limit | Purpose |
|---------|-------|---------|
| Max concurrent positions | 8 | Prevents overexposure |
| Max portfolio heat | 7% | Caps total account risk |
| Max same sector | 3 trades | Prevents correlation clustering (e.g., 4 tech stocks) |
| Max same asset class | 5 trades | Caps stock vs crypto concentration |
| Daily circuit breaker | 3 stops/day → 4h cool-down | Stops cascade losses after bad days |

## Implementation

### `portfolio_risk_guard.py` (new)
- `check_trade_allowed(strategy_id, ticker, asset_class, risk_pct)` — Pre-entry gate
- `record_stop_loss()` — Called when a trade hits its stop, increments daily counter
- `get_portfolio_status()` — Returns full risk dashboard for reporting
- Sector map covers 60+ stock tickers + crypto sub-classification
- Circuit breaker state persisted to `~/.hermes/market_data/daily_stops.json`

### Wiring
- `capture_signals.py`: Risk guard replaces old suspended heat cap. Blocks trades that fail any check.
- `capture_sweep_signals.py`: Same risk guard for STR-Q intraday trades. Circuit breaker records on stop hits.

## Test Results

Current portfolio state (6 open trades):
- 6/8 concurrent positions
- 4.5%/7.0% heat
- Technology: 2, Consumer Disc: 1, Crypto: 1, Unknown: 2
- A 6th stock trade would be blocked (max_same_asset_class = 5)
- A 3rd tech trade would be allowed (max_same_sector = 3)