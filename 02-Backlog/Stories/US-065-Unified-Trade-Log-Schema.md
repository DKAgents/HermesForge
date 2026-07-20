---
id: US-065
epic: EPIC-010
type: story
status: done
created: 2026-07-20
points: 3
tags: [paper-trading, schema, infrastructure]
---

# US-065: Unified Trade Log Schema (Stocks + Crypto)

## Story
As a paper trading system, I need one trade log schema that works for both stock and crypto signals, so that outcomes are directly comparable across asset classes and future exchange integrations (Alpaca, Hyperliquid) write to the same format.

## Acceptance Criteria
- [ ] CSV schema at `scripts/paper_trading/trades.csv` with columns:
  ```
  trade_id, strategy_id, ticker, asset_class (stock|crypto), data_source (yfinance|hyperliquid),
  direction (long|short), signal_id, entry_date, entry_price, stop_price, target_price,
  position_size_pct, position_size_units, quality_tier,
  status (open|closed), exit_date, exit_price, exit_reason (target|stop|time|invalidation),
  r_multiple, bars_held, subperiod, confirmation_level, weekly_gate_scaling,
  chart_path, notes
  ```
- [ ] `trade_id` format: `{strategy_id}_{ticker}_{entry_date}` (matches existing dedup `signal_id` convention from US-061 for traceability)
- [ ] Python module `scripts/paper_trading/trade_log.py` with:
  - `open_trade(trade_dict) -> trade_id` — appends a new open row
  - `close_trade(trade_id, exit_date, exit_price, exit_reason) -> None` — updates the row, computes r_multiple
  - `get_open_trades(strategy_id=None, ticker=None) -> list[dict]` — filterable
  - `has_open_trade(strategy_id, ticker) -> bool` — supports the max-1-open-per-(strategy,ticker) rule
- [ ] Unit tests: open a trade, verify has_open_trade True, close it, verify status updated and r_multiple computed correctly for both long and short

## Definition of Done
- trade_log.py passes unit tests
- Schema documented in this story and referenced by all downstream stories
- Committed to main
