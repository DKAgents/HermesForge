---
type: failure-mode
strategy_id: STR-20260726-outside-day-key-reversal
strategy_name: STR-N Outside Day Key Reversal
phase: 1A
verdict: KILL
reason: "Overall avg R -0.037 (below 0.2 threshold). Regime-dependent edge only in period3_current (+0.332). Phase 1B best variant +0.125."
metrics:
  r_expectancy: -0.037
  signals: 28
  win_rate: 46.4
  sub_periods_positive: 1
lesson: "Outside day key reversal has regime-dependent edge that only works in 2024+ period. Pre-2024 the reversal pattern fails in both bull and bear markets. Longer time stop (20 bars) helps but can't overcome pre-2024 drag. Pattern may become viable if current regime persists."
data_limitations: "Daily bars, survivorship bias, small period3 sample (15 signals)"
tags: [failure-mode, killed, outside-day, key-reversal, high-volatility, regime-dependent]
topic: strategies
confidence: high
has_quotes: false
source: HermesForge Strategies
---
# Failure Mode: STR-N Outside Day Key Reversal

## What Failed

Outside day + key reversal after a short-term decline in elevated volatility. The structural reversal pattern (engulfing range + close above prior close + volume confirmation) should be a strong signal, but overall edge is insufficient.

## Root Cause

1. **Regime-dependent edge**: period3_current (2024+) has +0.332 avg R, but period1_bull (2019-2021) has -0.516 and period2_bear (2022-2023) has -0.277
2. **Pre-2024 reversals are false**: Outside day reversals after declines in the 2019-2021 bull market were likely profit-taking dips that continued lower, not true reversal signals
3. **3:1 R:R never hit**: Zero target hits in baseline. 53.6% of trades exit at time stop
4. **Time stop too short**: Extending from 12→20 bars lifts avg R from -0.065 to +0.110, but still below 0.2
5. **Lowering target to 2:1 doesn't help**: The smaller target doesn't compensate for the reduced reward per win

## Lesson

- Outside day reversal patterns have **regime-dependent** edge, not universal edge
- The 2024+ period may reflect a structural change in market dynamics (AI rotation, retail participation, higher intraday volatility)
- Time stop length matters more than target ambition for this pattern
- A regime-gated version (only activate in "current regime" conditions) could be viable with more data

## Future Research Path

If the 2024+ regime persists, revisit STR-N with a regime-gate that only activates under conditions similar to period3_current. The +0.574 avg R (V5) in period3_current is promising but based on only 8 signals — need more data to confirm it's structural.

## Related

- [[STR-N-phase1a]]
- [[STR-20260726-outside-day-key-reversal|STR-N Strategy]]
- [[REGIME-high-volatility]]
- [[N004-outside-day-as-reversal-confirmation]]