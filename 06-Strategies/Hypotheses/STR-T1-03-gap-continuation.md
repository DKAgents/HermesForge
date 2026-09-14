---
id: STR-T1-03-gap-continuation
type: strategy
status: watch
asset_class: both
trade_style: swing
timeframe: daily
market_regime: trending
core_idea: breakout
confidence: medium
publish_enabled: false
publish_channel: stocks
evidence_links:
  - STR-T1-discovered-strategies
last_reviewed: 2026-09-13
created: 2026-09-13
updated: 2026-09-13
origin: T1 Strategy Discovery (Aegis Rebuild)
tags: [strategy, gap, continuation, breakout, daily, t0-entry, hostile-fill, t1]
topic: strategies
has_quotes: false
source: Murphy Gap Theory + T1 Discovery
scanner_module: scanner_t1_03_gap_continuation
scanner_alias: scan_t1_03
strategy_id: STR-T1-03-gap-continuation
scan_mode: per_ticker
---

# STR-T1-03: Gap Continuation (Daily)

## Origin
Gap theory (Murphy Chapter on Gaps). Overnight gaps that continue rather than fade represent persistent order imbalance. The only T1 strategy with true t+0 entry — the gap itself IS the signal, and entry occurs on the gap day, completely sidestepping the t+1 fill penalty.

## Signal Rules

### Long
1. Trend: 50-day SMA > 200-day SMA (bull market)
2. Gap: today's open > prior day's high by ≥ 0.5 ATR(14)
3. Continuation: close > open (gap holding)
4. Volume: today's volume > prior 5-day average × 1.2

### Short
Mirror: bear market trend, gap down ≥ 0.5 ATR, continuation confirmed.

## Entry/Exit
- Entry: Market order at close of gap day (t+0)
- Stop: Prior day's close (gap fill). Min 0.5 ATR(14)
- Target T1 (50%): 1.5 × gap size
- Target T2 (50%): Trail with 5-day EMA
- Time Stop: 5 trading days