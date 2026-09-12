---
type: insight
date: 2026-09-12
actionability: 4
connection_type: adds_condition
domains: [indicators, patterns, rules]
sources: ["N013-volume-as-a-filter-for-false-breakouts", "R052-filters-for-confirming-breakouts", "N028-bull-trap-false-upside-breakout"]
seed_id: breakout_volume_risk
tags: [insight, discovery, knowledge-evolution]
---

# Volume-Confirmed Breakout Stop Placement Strategy

## Discovery Summary

N013 and N028 establish that valid breakouts have heavy volume while bull traps feature light-volume breakouts followed by heavy-volume declines. R052 provides multiple confirmation filters (close beyond peak, percentage penetration, two-day rule). Combining these: a trader can place initial stops just below the breakout level, but only move stops to breakeven or trail them after volume confirms the breakout is valid — if a breakout occurs on light volume, the stop remains tight because the probability of a bull trap reversal on heavy volume is elevated.

## Trading Implication

Enter on breakouts meeting R052 price filters, but delay stop-loss widening or breakeven adjustment until heavy volume confirms the breakout per N013; if volume is light, keep the initial stop tight below the breakout zone to exit quickly on the heavy-volume reversal that N028 warns about.

## Supporting Notes

- [[N013-volume-as-a-filter-for-false-breakouts]]
- [[R052-filters-for-confirming-breakouts]]
- [[N028-bull-trap-false-upside-breakout]]

## Connection Type

**adds_condition** — Actionability score: 4/5
