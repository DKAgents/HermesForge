---
type: insight
date: 2026-09-15
actionability: 4
connection_type: adds_condition
domains: [indicators, patterns, rules]
sources: ["N013-volume-as-a-filter-for-false-breakouts", "R052-filters-for-confirming-breakouts", "N028-bull-trap-false-upside-breakout"]
seed_id: breakout_volume_risk
tags: [insight, discovery, knowledge-evolution]
topic: knowledge
confidence: high
has_quotes: false
source: unknown
---
# Volume Filter for Stop Placement on Breakouts

## Discovery Summary

Combining the volume filter (N013) with the breakout confirmation criteria (R052) and the bull trap pattern (N028) provides a clear rule: a breakout on light volume indicates a potential false breakout, so stops should be placed tighter (e.g., just below the breakout level) to protect against the subsequent heavy-volume decline. Conversely, a high-volume breakout confirms validity and allows wider stops.

## Trading Implication

On any breakout, check volume: if light, treat as a bull trap and set a stop just below the breakout point; if heavy, use a standard trailing stop or wider stop to ride the trend.

## Supporting Notes

- [[N013-volume-as-a-filter-for-false-breakouts]]
- [[R052-filters-for-confirming-breakouts]]
- [[N028-bull-trap-false-upside-breakout]]

## Connection Type

**adds_condition** — Actionability score: 4/5
