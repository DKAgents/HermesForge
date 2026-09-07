---
type: insight
date: 2026-09-07
actionability: 4
connection_type: adds_condition
domains: [indicators, patterns, rules]
sources: ["N013-volume-as-a-filter-for-false-breakouts", "R052-filters-for-confirming-breakouts", "N028-bull-trap-false-upside-breakout"]
seed_id: breakout_volume_risk
tags: [insight, discovery, knowledge-evolution]
---

# Volume-confirmed breakout stop placement strategy

## Discovery Summary

N013 establishes that valid breakouts have heavy volume while false breakouts (bull traps) occur on light volume. N028 reinforces that a light-volume upside breakout followed by heavy-volume decline is a negative combination signaling a bull trap. R052 provides confirmation filters like requiring a close beyond resistance. Combining these: a trader can use volume as a condition to validate a breakout before entry, and if a light-volume breakout fails with heavy-volume decline, place a stop just below the breakout level to exit quickly, as this specific volume pattern (per N028) signals the trap is confirmed and downside momentum is strong.

## Trading Implication

Enter only on breakouts with above-average volume and a close beyond resistance (per R052). If a breakout occurs on light volume and subsequent price declines on heavy volume, immediately exit or place a tight stop below the breakout level, as this volume sequence confirms a bull trap per N028.

## Supporting Notes

- [[N013-volume-as-a-filter-for-false-breakouts]]
- [[R052-filters-for-confirming-breakouts]]
- [[N028-bull-trap-false-upside-breakout]]

## Connection Type

**adds_condition** — Actionability score: 4/5
