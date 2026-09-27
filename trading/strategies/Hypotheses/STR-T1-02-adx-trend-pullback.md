---
id: STR-T1-02-adx-trend-pullback
type: strategy
status: watch
asset_class: both
trade_style: swing
timeframe: daily
market_regime: trending
core_idea: trend_following
confidence: medium
publish_enabled: false
publish_channel: stocks
evidence_links:
  - STR-T1-discovered-strategies
last_reviewed: 2026-09-13
created: 2026-09-13
updated: 2026-09-13
origin: T1 Strategy Discovery (Aegis Rebuild)
tags: [strategy, trend, adx, pullback, ema, daily, hostile-fill, t1]
topic: strategies
has_quotes: false
source: Murphy ADX/DMI + DXP Analytics intraday adaptation
scanner_module: scanner_t1_02_adx_pullback
scanner_alias: scan_t1_02
strategy_id: STR-T1-02-adx-trend-pullback
scan_mode: per_ticker
---

# STR-T1-02: ADX Trend Continuation Pullback (Daily)

## Origin
Murphy Chapters on trend identification (ADX/DMI) and moving averages. DXP Analytics intraday adaption confirmed institutional EMA-respecting behavior. Adapted for daily-bar hostile-fill survivability.

## Signal Rules

### Long
1. Trend filter: ADX(14) > 25 AND +DI > −DI
2. Pullback: today's low touches or falls within 0.3 ATR(14) of 20-day EMA
3. Reversal candle: close > open
4. Volume: today's volume < prior 5-day average (declining vol on pullback)

### Short
Mirror: ADX > 25, -DI > +DI, rally to EMA, bearish close, declining volume.

## Entry/Exit
- Entry: Market order at next day's open (t+1)
- Stop: Beyond pullback bar extreme ± 0.2 ATR(14). Min 1.5 ATR(14)
- Target T1 (50%): Prior 20-bar swing extreme
- Target T2 (50%): Trail with 20-day EMA
- Time Stop: 15 trading days