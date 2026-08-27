---
type: insight
date: 2026-08-27
actionability: 4
connection_type: adds_condition
domains: [indicators, patterns, rules]
sources: ["N013-volume-as-a-filter-for-false-breakouts", "R052-filters-for-confirming-breakouts", "N028-bull-trap-false-upside-breakout"]
seed_id: breakout_volume_risk
tags: [insight, discovery, knowledge-evolution]
---

# Volume-Confirmed Breakout with Structured Stop Placement

## Discovery Summary

N013 states that valid upside breakouts require heavy volume, while false breakouts (bull traps) occur on light volume. N028 describes the bull trap pattern where a light-volume upside breakout reverses sharply on heavy volume. R052 provides specific confirmation filters (close beyond peak, percentage penetration, two-day rule) that, when combined with the volume analysis from N013 and N028, create a structured entry filter. The missing stop component can be derived: if a breakout fails the volume and confirmation tests, the logical stop placement is just below the breakout level where the bull trap's heavy-volume decline would confirm the failure.

## Trading Implication

Enter only on breakouts that satisfy both R052's confirmation filters and N013's heavy-volume requirement; place an initial stop immediately below the breakout level, and exit immediately if a subsequent decline occurs on heavy volume per N028's negative chart combination.

## Supporting Notes

- [[N013-volume-as-a-filter-for-false-breakouts]]
- [[R052-filters-for-confirming-breakouts]]
- [[N028-bull-trap-false-upside-breakout]]

## Connection Type

**adds_condition** — Actionability score: 4/5
