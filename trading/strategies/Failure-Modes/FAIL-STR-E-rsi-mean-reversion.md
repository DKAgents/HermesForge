---
type: failure-mode
strategy_id: STR-20260726-rsi-mean-reversion-entry
strategy_name: RSI Mean-Reversion
phase: 1A
verdict: KILL
reason: "Negative avg R after costs (-0.056R). RSI threshold crossback produces no statistical edge."
metrics:
  r_expectancy: -0.056
  signals: 12042
  win_rate: 38.0
  sub_periods_positive: 0
lesson: "RSI mean-reversion on daily bars without regime filter produces too many false signals in trending markets. Short signals dominate (65% of signals) and fight the dominant uptrend. CCI with crossover-at-extreme (STR-J) is structurally better."
data_limitations: "Daily bars, survivorship bias"
tags: [failure-mode, killed, rsi, mean-reversion]
topic: strategies
confidence: high
has_quotes: false
source: HermesForge Strategies
---
# Failure Mode: STR-E RSI Mean-Reversion

## What Failed

RSI(14) crossing back through 30 (long) or 70 (short) as a mean-reversion entry. The crossover-confirmation entry did not produce a statistical edge across 216 tickers.

## Root Cause

1. No regime filter — strategy fades trends in trending markets
2. Short signals dominate (65%) and fight the structural uptrend in equities
3. Stop hit 46.6% of the time vs target only 13.6% — entries are premature

## Lesson for Future Strategies

- Mean-reversion needs a regime filter (only trade in ranging markets)
- Shorting at overbought levels fails in equities due to structural positive drift
- CCI with crossover-at-extreme (STR-J) outperforms: +0.222R vs -0.056R
- See: [[STR-20260726-eufearia-cci-reversal|STR-J]] which succeeded where STR-E failed

## Related
- [[STR-E-phase1a]]
- [[STR-20260726-rsi-mean-reversion-entry|STR-E Strategy]]
- [[REGIME-trending]]
- [[REGIME-ranging]]
