---
type: insight
date: 2026-08-21
actionability: 4
connection_type: creates_filter
domains: [indicators, patterns, rules]
sources: ["N013-volume-as-a-filter-for-false-breakouts", "R052-filters-for-confirming-breakouts", "N028-bull-trap-false-upside-breakout"]
seed_id: breakout_volume_risk
tags: [insight, discovery, knowledge-evolution]
topic: knowledge
confidence: high
has_quotes: false
source: unknown
---
# Multi-Filter Breakout System With Volume-Based Stop Placement

## Discovery Summary

N013 and N028 establish that light-volume breakouts followed by heavy-volume declines signal false breakouts (bull traps), while R052 provides a complementary set of price-based confirmation filters (close beyond resistance, percentage penetration, two-day rule, Friday close). Together, these three notes create a layered confirmation system: price-based filters from R052 must be satisfied first, then volume from N013/N028 must confirm. Critically, N028's description of the bull trap pattern implies a specific stop-placement rule not explicitly stated in any single note: if a breakout passes price filters but fails the volume test (light volume up, heavy volume decline), a short entry or stop-exit below the breakout level is warranted.

## Trading Implication

A trader should only act on breakouts that satisfy at least one price filter from R052 AND show heavy volume on the breakout day; if a breakout clears resistance on light volume and is then followed by a heavy-volume down day, treat the breakout level as a stop-loss trigger and exit or reverse immediately.

## Supporting Notes

- [[N013-volume-as-a-filter-for-false-breakouts]]
- [[R052-filters-for-confirming-breakouts]]
- [[N028-bull-trap-false-upside-breakout]]

## Connection Type

**creates_filter** — Actionability score: 4/5
