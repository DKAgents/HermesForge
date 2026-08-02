---
type: backtest-result
strategy_id: STR-20260728-adaptive-trend
strategy_name: AdaptiveTrend
phase: 1A
asset_class: stocks
direction: long-only
universe: 529 tickers
period_start: 2019-04-01
period_end: 2026-07-17
signals_per_year: 266.3
avg_r: 0.231
win_rate: 43.2
sub_periods_positive: "3/3 (bull +0.172, bear +0.193, current +0.305)"
verdict: WATCH
verdict_reason: "Positive in all sub-periods but avg R < 0.5 friction flag"
data_limitations: "Daily bars (paper uses 6h), survivorship bias, no transaction costs"
produced_by: "[[Backtester]]"
tags: [backtest, phase1a, STR-I, stocks]
topic: strategies
confidence: high
has_quotes: false
source: HermesForge Strategies
---
# STR-I Phase 1A Results

## Key Findings

1. Long-only essential for stocks — shorts avg R = -0.149 (29.4% win rate)
2. SMA200 trend filter critical — eliminates counter-trend noise
3. Theta=0.20 optimal for daily bars
4. Alpha=2.0 outperforms 2.5 — smaller losses when wrong
5. Top performers: NVDA (+1.15R), HOOD (+1.06), INTC (+0.91), MRNA (+0.90)

## Parameters
- L = 10, theta = 0.20, alpha = 2.0, max_bars = 120, SMA200 filter

## Related
- [[STR-20260728-adaptive-trend|STR-I Strategy]]
- [[STR-I-phase1b2-stocks]]
- [[STR-I-phase1b2-crypto]]
- [[ADR-004-Phase1-Validation-Framework]]
- [[REGIME-trending]]
