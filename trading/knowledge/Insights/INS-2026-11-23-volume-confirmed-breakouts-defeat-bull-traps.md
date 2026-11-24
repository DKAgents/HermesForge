---
type: insight
date: 2026-11-23
actionability: 4
connection_type: adds_condition
domains: [indicators, patterns, rules]
sources: ["N013-volume-as-a-filter-for-false-breakouts", "R052-filters-for-confirming-breakouts", "N028-bull-trap-false-upside-breakout"]
seed_id: breakout_volume_risk
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# Volume-Confirmed Breakouts Defeat Bull Traps

## Discovery Summary

R052-filters-for-confirming-breakouts provides price-based confirmation (close beyond resistance, percentage penetration, two-day rule) but omits volume. N013-volume-as-a-filter-for-false-breakouts adds the missing condition: valid upside breakouts need heavy volume, and a light-volume breakout followed by a heavy-volume decline is a negative chart combination. That sequence is exactly the bull trap in N028-bull-trap-false-upside-breakout. Therefore, traders should combine R052's price filters with N013's volume condition to avoid entering or to exit the bull trap.

## Trading Implication

Treat a light-volume upside breakout as suspect; if price later falls below the breakout level on heavy volume, exit longs rather than waiting for a deeper stop. For entries, require a close beyond resistance on above-average volume before acting on a breakout.

## Supporting Notes

- [[N013-volume-as-a-filter-for-false-breakouts]]
- [[R052-filters-for-confirming-breakouts]]
- [[N028-bull-trap-false-upside-breakout]]

## Connection Type

**adds_condition** — Actionability score: 4/5
