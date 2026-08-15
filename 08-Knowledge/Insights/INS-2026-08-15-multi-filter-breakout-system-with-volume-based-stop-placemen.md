---
type: insight
date: 2026-08-15
actionability: 4
connection_type: creates_filter
domains: [indicators, patterns, rules]
sources: ["N013-volume-as-a-filter-for-false-breakouts", "R052-filters-for-confirming-breakouts", "N028-bull-trap-false-upside-breakout"]
seed_id: breakout_volume_risk
tags: [insight, discovery, knowledge-evolution]
---

# Multi-Filter Breakout System with Volume-Based Stop Placement

## Discovery Summary

R052 provides structural filters (close beyond resistance, percentage penetration, two-day rule, Friday close) to confirm breakouts, while N013 and N028 together specify that volume is the critical diagnostic: a light-volume breakout followed by heavy-volume decline is the signature of a bull trap. The non-obvious connection is that these filters should be applied sequentially — price-based filters (R052) screen initial entry, but volume behavior post-breakout (N013, N028) determines whether to hold the position or reverse it with a stop. N028 adds the macro context that bull traps are most dangerous at major market tops, making the volume divergence signal especially urgent there.

## Trading Implication

A trader should require both price confirmation (close beyond resistance, ideally two consecutive closes or a Friday close per R052) AND expanding volume on the breakout; if volume is light on the breakout and then surges on the subsequent reversal, treat the position as a failed breakout and exit immediately, placing a stop just above the false breakout high to cap loss on any short entry.

## Supporting Notes

- [[N013-volume-as-a-filter-for-false-breakouts]]
- [[R052-filters-for-confirming-breakouts]]
- [[N028-bull-trap-false-upside-breakout]]

## Connection Type

**creates_filter** — Actionability score: 4/5
