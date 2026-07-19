---
id: US-059
epic: EPIC-009
type: story
status: backlog
created: 2026-07-20
points: 5
tags: [discord, charts, mplfinance, visualization]
depends-on: US-054
---

# US-059: Chart Image Generator

## Story
As a signal publisher, I need a Python function that generates an annotated chart PNG for a given trade setup, so that Discord alerts include a visual representation of the signal.

## Acceptance Criteria
- [ ] Function `generate_setup_chart(ticker, signal_dict, output_path)` in `scripts/discord/chart_generator.py`
- [ ] Chart shows:
  - Last 60 daily OHLCV bars (candlestick style, dark theme)
  - MACD indicator panel below price (lines + histogram)
  - RSI indicator panel (14-period)
  - Three horizontal lines on price panel:
    - Green dashed: entry price, labelled "Entry $XXX"
    - Red dashed: stop price, labelled "Stop $XXX"
    - Blue dashed: target price, labelled "Target $XXX"
  - Vertical arrow or marker at signal bar
  - Title: "{TICKER} — {STRATEGY_NAME} — {DATE}"
- [ ] Uses mplfinance + matplotlib (already installed)
- [ ] Loads OHLCV from cached parquet files (`~/.hermes/market_data/`)
- [ ] Returns path to saved PNG file
- [ ] Chart size: 1200×800px minimum (readable on Discord)
- [ ] Smoke test: generate chart for SPY using a synthetic signal dict, verify PNG created

## Signal Dict Schema
```python
{
  "ticker": "NVDA",
  "date": "2026-07-20",
  "direction": "short",
  "entry_price": 875.00,
  "stop_price": 882.50,
  "target_price": 850.00,
  "r_multiple": 3.33,
  "strategy_id": "STR-B-macd-histogram-divergence",
  "strategy_version": "1.1",
  "confirmation_level": "Level 1",
  "subperiod": "period3_current"
}
```

## Definition of Done
- chart_generator.py runnable standalone
- Smoke test produces valid PNG
- Committed to main
