---
type: insight
date: 2026-10-04
actionability: 4
connection_type: creates_filter
domains: [indicators, patterns, rules]
sources: ["N013-volume-as-a-filter-for-false-breakouts", "R052-filters-for-confirming-breakouts", "N028-bull-trap-false-upside-breakout"]
seed_id: breakout_volume_risk
tags: [insight, discovery, knowledge-evolution]
---

# Volume filter to avoid bull trap stops

## Discovery Summary

The notes N013 (volume as a filter for false breakouts) and R052 (filters for confirming breakouts) together indicate that low volume on a breakout signals a potential bull trap as described in N028. This combination allows a trader to identify false upside breakouts and adjust stop placement accordingly.

## Trading Implication

When a breakout occurs with insufficient volume, treat it as a possible bull trap and place a stop just beyond the breakout point to protect against the reversal.

## Supporting Notes

- [[N013-volume-as-a-filter-for-false-breakouts]]
- [[R052-filters-for-confirming-breakouts]]
- [[N028-bull-trap-false-upside-breakout]]

## Connection Type

**creates_filter** — Actionability score: 4/5
