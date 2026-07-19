---
type: insight
date: 2026-07-19
actionability: 4
connection_type: creates_filter
domains: [indicators, patterns, rules]
sources: ["N013-volume-as-a-filter-for-false-breakouts", "R052-filters-for-confirming-breakouts", "N028-bull-trap-false-upside-breakout"]
seed_id: breakout_volume_risk
tags: [insight, discovery, knowledge-evolution]
---

# Multi-Filter Breakout System With Volume-Based Stop Trigger

## Discovery Summary

R052 provides a hierarchy of confirmation filters (close beyond resistance, percentage penetration, two-day rule, Friday close) while N013 and N028 both emphasize that volume is a critical but incomplete filter for distinguishing valid breakouts from bull traps. The non-obvious connection is that these filters can be layered sequentially: first apply the structural filters from R052 to establish a breakout, then use the volume signature from N013/N028 as a final validation gate — specifically, a light-volume breakout that fails even one of R052's structural filters should immediately trigger stop placement below the breakout level, since N028 identifies the subsequent heavy-volume decline as confirming the trap.

## Trading Implication

On any upside breakout, require at least two of R052's structural filters to be satisfied AND confirm heavy volume; if volume is light on the breakout day, set a tight stop just below the breakout level immediately, as N028 warns the subsequent decline confirming the bull trap will arrive on heavy volume — waiting for that confirmation is too late to exit without significant loss.

## Supporting Notes

- [[N013-volume-as-a-filter-for-false-breakouts]]
- [[R052-filters-for-confirming-breakouts]]
- [[N028-bull-trap-false-upside-breakout]]

## Connection Type

**creates_filter** — Actionability score: 4/5
