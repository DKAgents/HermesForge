---
type: backtest-result
strategy_id: STR-20260730-breadth-gated-gap-reversal
strategy_name: Breadth-Gated Gap Reversal
phase: 1A
asset_class: stocks
direction: long-only
universe: 529 tickers
period_start: 2019-04-01
period_end: 2026-07-30
signals_per_year: 0
avg_r: null
win_rate: null
trade_count: 0
verdict: KILL
verdict_reason: "0 signals across 529 tickers over 7 years. Breadth filter (McClellan < -50) combined with gap-down detection and gap-midpoint crossover produces zero trades."
data_limitations: "Daily bars, survivorship bias, breadth computed from 529-stock universe (not full NYSE/NASDAQ)"
produced_by: "[[Backtester]]"
tags: [backtest, phase1a, STR-K, stocks, kill]
topic: strategies
confidence: high
has_quotes: false
source: HermesForge Strategies
---
# STR-K Phase 1A Results

## Summary

Zero signals found across 529 tickers over ~7 years. The strategy is killed at Phase 1A.

## Root Cause Analysis

The compound filter is too restrictive:

1. **McClellan Oscillator < -50:** Only 48 out of 1,967 days (2.4%) meet this condition
2. **AD Line trending up (3-day):** Further reduces the qualifying days
3. **Gap down >= 1.5 ATR:** Requires a significant gap on those specific days
4. **Gap midpoint crossover:** Price must cross the midpoint on the same or next day

The intersection of all four conditions produces zero trades. The breadth filter is the primary bottleneck — only 2.4% of days qualify, and the probability of a significant gap-down on those exact days is low.

## Lesson

This is the same pattern as STR-H (too many filters compound). The breadth gate is conceptually sound (regime filter for gap exhaustion), but:
- The McClellan < -50 threshold is too extreme (should try < -30 or < -20)
- The gap requirement (1.5 ATR) is too large (should try 0.5 or 1.0 ATR)
- The midpoint crossover requirement adds another gate (should check if any gap fill at all is sufficient)

## Phase 1B Opportunity

If pursued, the strategy needs loosening:
- McClellan threshold: -50 → -30 (4x more qualifying days)
- Gap threshold: 1.5 ATR → 0.75 ATR (2x more gaps detected)
- Remove midpoint crossover (enter at open instead)
- This would produce enough signals to evaluate the edge

However, the zero-signal result suggests the core concept (breadth-gated gap reversal) may be too niche for daily-bar scanning. The strategy might work better with intraday data where gap fills are more granular.

## Related
- [[STR-20260730-breadth-gated-gap-reversal|STR-K Strategy]]
- [[FAIL-STR-H-first-pullback]]
- [[ADR-004-Phase1-Validation-Framework]]
- [[REGIME-transitional]]