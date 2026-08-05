---
type: insight
date: 2026-08-03
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
# Volume-Confirmed Breakout Filter With Stop Placement Logic

## Discovery Summary

N013 and N028 together establish that light-volume breakouts followed by heavy-volume declines are the diagnostic signature of a bull trap. R052 provides the structural confirmation filters (close-beyond, percentage criterion, two-day rule, Friday close) that must be satisfied before treating any breakout as valid. The non-obvious connection is that these filters from R052 function as a sequenced checklist: a breakout that clears structural filters (R052) but fails the volume test (N013/N028) is a higher-probability false breakout than either criterion alone, enabling a specific short-entry trigger rather than just avoidance.

## Trading Implication

A trader should enter a counter-trend short (or exit long positions) when a breakout satisfies structural price filters from R052 (e.g., closes above resistance) but occurs on light volume, then is followed by a heavy-volume down day — placing a stop just above the false breakout high as the invalidation level.

## Supporting Notes

- [[N013-volume-as-a-filter-for-false-breakouts]]
- [[R052-filters-for-confirming-breakouts]]
- [[N028-bull-trap-false-upside-breakout]]

## Connection Type

**creates_filter** — Actionability score: 4/5
