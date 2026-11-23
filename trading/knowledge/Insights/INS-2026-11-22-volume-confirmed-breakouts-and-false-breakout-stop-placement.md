---
type: insight
date: 2026-11-22
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
# Volume-confirmed breakouts and false breakout stop placement

## Discovery Summary

The volume filter from N013 and the bull trap pattern N028 both identify false breakouts by combining light-volume upside penetration with a subsequent heavy-volume decline. R052 adds structural filters (close beyond resistance, percentage penetration, two-day rule) to confirm breakouts. Together, these notes imply a conditional stop strategy: only treat a breakout as valid if it passes R052's price filters and shows heavy volume; if a breakout is on light volume, place a tighter stop or prepare to exit when a heavy-volume decline occurs below the breakout level.

## Trading Implication

After a breakout, check volume: if light, reduce position size or set a stop just below the breakout level; if price subsequently declines on heavy volume, treat it as a bull trap and exit immediately. If volume is heavy on the breakout, hold with a normal stop and trust the valid breakout.

## Supporting Notes

- [[N013-volume-as-a-filter-for-false-breakouts]]
- [[R052-filters-for-confirming-breakouts]]
- [[N028-bull-trap-false-upside-breakout]]

## Connection Type

**adds_condition** — Actionability score: 4/5
