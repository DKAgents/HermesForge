---
type: insight
date: 2026-09-21
actionability: 3
connection_type: adds_condition
domains: [indicators, patterns, rules]
sources: ["N013-volume-as-a-filter-for-false-breakouts", "R052-filters-for-confirming-breakouts", "N028-bull-trap-false-upside-breakout"]
seed_id: breakout_volume_risk
tags: [insight, discovery, knowledge-evolution]
---

# Volume-based stop placement for false breakouts

## Discovery Summary

N013 (Volume as a Filter for False Breakouts) warns that a valid breakout needs heavy volume, while a false breakout often shows light volume followed by a heavy-volume decline. R052 (Filters for Confirming Breakouts) provides additional confirmation rules (close beyond resistance, percentage penetration, etc.). N028 (Bull Trap) explicitly describes the light-volume breakout / heavy-volume decline pattern as a negative combination. Together, these notes suggest that when a breakout occurs on light volume, a trader should place a stop just below the breakout level or use a trailing stop, because the pattern may be a bull trap that reverses sharply on heavy volume.

## Trading Implication

After a breakout on light volume, set a tighter stop (e.g., just below the breakout point or the recent swing low) to exit quickly if a heavy-volume decline materializes, confirming a bull trap.

## Supporting Notes

- [[N013-volume-as-a-filter-for-false-breakouts]]
- [[R052-filters-for-confirming-breakouts]]
- [[N028-bull-trap-false-upside-breakout]]

## Connection Type

**adds_condition** — Actionability score: 3/5
