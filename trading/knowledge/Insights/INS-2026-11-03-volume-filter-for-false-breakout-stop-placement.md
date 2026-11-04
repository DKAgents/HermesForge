---
type: insight
date: 2026-11-03
actionability: 4
connection_type: reveals_sequence
domains: [indicators, patterns, risk guidelines, trading rules]
sources: ["N013-volume-as-a-filter-for-false-breakouts", "R052-filters-for-confirming-breakouts", "N028-bull-trap-false-upside-breakout"]
seed_id: breakout_volume_risk
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# Volume Filter for False Breakout Stop Placement

## Discovery Summary

N013 and N028 both establish that a false upside breakout often occurs on light volume and is confirmed by a subsequent decline on heavy volume. R052 adds confirmation filters such as closes beyond resistance and volume examination. Together, they imply a sequence: a light-volume breakout signals caution, and a heavy-volume decline after that breakout confirms the false breakout, providing a clear trigger for stop placement or exit.

## Trading Implication

After an upside breakout, check volume; if it is light, avoid entering or place a stop just below the breakout level. If price subsequently declines on heavy volume, exit immediately because the breakout is likely a bull trap.

## Supporting Notes

- [[N013-volume-as-a-filter-for-false-breakouts]]
- [[R052-filters-for-confirming-breakouts]]
- [[N028-bull-trap-false-upside-breakout]]

## Connection Type

**reveals_sequence** — Actionability score: 4/5
