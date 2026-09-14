---
id: STR-T1-01-outside-day-key-reversal
type: strategy
status: watch
asset_class: both
trade_style: swing
timeframe: daily
market_regime: high_vol_reversal
core_idea: reversal
confidence: medium
publish_enabled: false
publish_channel: stocks
evidence_links:
  - STR-T1-discovered-strategies
last_reviewed: 2026-09-13
created: 2026-09-13
updated: 2026-09-13
origin: T1 Strategy Discovery (Aegis Rebuild)
tags: [strategy, reversal, outside-day, key-reversal, murphy, t1, daily, hostile-fill]
topic: strategies
has_quotes: false
source: Murphy Technical Analysis Ch4 + T1 Discovery
scanner_module: scanner_t1_01_outside_day
scanner_alias: scan_t1_01
strategy_id: STR-T1-01-outside-day-key-reversal
scan_mode: per_ticker
---

# STR-T1-01: Outside Day Key Reversal (Daily)

## Origin
Murphy Chapter 4 (Reversal Patterns), "Key Reversal Day" — in an uptrend, price makes a new high then closes below the prior day's close. Already flagged as STR-N with paper Mean R = +0.41, 71% WR (14 signals). T1 Discovery refined the specification with hostile-fill-aware entry/exit rules.

## Signal Rules

### Long (Bottom Reversal)
1. Prior trend: price closed below 20-day SMA
2. Signal bar: today's low < prior 5-day low AND today's close > prior day's close AND today's range > prior 5-day average range × 1.2
3. Confirmation: signal bar close > signal bar open (bullish close)

### Short (Top Reversal)
Mirror conditions with close < open on wide-range outside bar.

## Entry/Exit
- Entry: Market order at next day's open (t+1)
- Stop: Beyond signal bar extreme ± 0.2 ATR(14). Min 0.5% (stocks) / 1.0% (crypto)
- Target T1 (50%): 1.5R | T2 (50%): 3.0R or prior swing high/low
- Time Stop: 10 trading days