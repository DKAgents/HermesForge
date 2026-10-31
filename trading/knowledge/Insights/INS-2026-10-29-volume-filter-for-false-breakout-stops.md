---
type: insight
date: 2026-10-29
actionability: 3
connection_type: adds_condition
domains: [indicators, patterns, rules]
sources: ["N013-volume-as-a-filter-for-false-breakouts", "R052-filters-for-confirming-breakouts"]
seed_id: breakout_volume_risk
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# Volume filter for false breakout stops

## Discovery Summary

Note N013 (volume-as-a-filter-for-false-breakouts) suggests using volume to avoid false breakouts. Rule R052 (filters-for-confirming-breakouts) outlines general confirmation filters. Together, they imply that a breakout lacking sufficient volume is likely false, which warrants placing a tighter stop or exiting immediately. This combines volume confirmation with stop placement for false breakout scenarios.

## Trading Implication

When entering a breakout, only hold if volume exceeds a threshold (e.g., 1.5x average); if volume is low, place a stop just below the breakout level to exit quickly on false moves.

## Supporting Notes

- [[N013-volume-as-a-filter-for-false-breakouts]]
- [[R052-filters-for-confirming-breakouts]]

## Connection Type

**adds_condition** — Actionability score: 3/5
