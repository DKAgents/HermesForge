---
type: insight
date: 2026-08-28
actionability: 3
connection_type: adds_condition
domains: [indicators, patterns, rules]
sources: ["N013-volume-as-a-filter-for-false-breakouts", "R052-filters-for-confirming-breakouts", "N028-bull-trap-false-upside-breakout"]
seed_id: breakout_volume_risk
tags: [insight, discovery, knowledge-evolution]
---

# Volume and price filters combine to avoid bull traps

## Discovery Summary

N013 emphasizes that valid upside breakouts need heavy volume, while false breakouts show light volume followed by heavy selling. N028 describes the bull trap as a false upside breakout, often with light volume then heavy decline. R052 lists price-based confirmation filters (close beyond peak, percentage penetration, two-day rule) for breakouts. Together, these notes suggest that combining volume analysis with price confirmation rules can filter out false breakouts and bull traps more effectively than either alone.

## Trading Implication

A trader should require both a confirming price close (e.g., above a prior peak per R052) and heavy volume (per N013) before acting on an upside breakout; if volume is light, avoid entry or place a tight stop below the breakout level.

## Supporting Notes

- [[N013-volume-as-a-filter-for-false-breakouts]]
- [[R052-filters-for-confirming-breakouts]]
- [[N028-bull-trap-false-upside-breakout]]

## Connection Type

**adds_condition** — Actionability score: 3/5
