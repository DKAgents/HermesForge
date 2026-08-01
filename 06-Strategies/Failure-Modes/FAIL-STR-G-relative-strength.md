---
type: failure-mode
strategy_id: STR-20260726-relative-strength-sector-rotation-entry
strategy_name: Relative Strength Sector Rotation
phase: 1A
verdict: KILL
reason: "Avg R 0.105 < 0.2 kill threshold. RS-crossover generates 1,244 signals/year but with razor-thin edge."
metrics:
  r_expectancy: 0.105
  signals: 8830
  win_rate: 52.2
  sub_periods_positive: 0
lesson: "RS-crossover alone is too easily triggered by short-term noise. Needs stricter/slower breakout definition (longer SMA, RS at N-bar high, or minimum RS_ROC magnitude)."
data_limitations: "Daily bars, survivorship bias"
tags: [failure-mode, killed, relative-strength, sector-rotation]
---

# Failure Mode: STR-G Relative Strength

## What Failed

Relative strength crossover (stock RS ratio crossing above its SMA) as a rotation signal. Extremely high signal count but razor-thin edge per trade.

## Root Cause

1. RS-crossover triggers on noise, not genuine rotation
2. Only 5.6% of trades reach the 2.5:1 target
3. 71% exit at time stop — small median drift, not directional continuation

## Lesson

- RS signals need stricter confirmation (longer SMA, N-bar high, minimum ROC)
- High signal frequency with thin edge = whipsaw, not rotation
- Consider weekly RS rather than daily for less noise

## Related
- [[STR-G-phase1a]]
- [[STR-20260726-relative-strength-sector-rotation-entry|STR-G Strategy]]
