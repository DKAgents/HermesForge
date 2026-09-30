---
type: insight
date: 2026-09-29
actionability: 4
connection_type: creates_filter
domains: [indicators, patterns, rules]
sources: ["N013-volume-as-a-filter-for-false-breakouts", "R052-filters-for-confirming-breakouts", "N028-bull-trap-false-upside-breakout"]
seed_id: breakout_volume_risk
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# Volume filter for bull trap stops

## Discovery Summary

N028 describes a bull trap as a false upside breakout. N013 recommends using volume to filter false breakouts, and R052 outlines filters for confirming breakouts. Combining these, a low-volume breakout above resistance signals a potential bull trap, allowing traders to place a stop loss just below the breakout level instead of chasing the move.

## Trading Implication

On a breakout above resistance, if volume is below average or declining, treat it as a potential bull trap and enter a short position with a stop just above the breakout, or avoid longs altogether.

## Supporting Notes

- [[N013-volume-as-a-filter-for-false-breakouts]]
- [[R052-filters-for-confirming-breakouts]]
- [[N028-bull-trap-false-upside-breakout]]

## Connection Type

**creates_filter** — Actionability score: 4/5
