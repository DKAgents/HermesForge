---
type: insight
date: 2026-10-26
actionability: 4
connection_type: adds_condition
domains: [indicators, patterns, risk_management, trading_rules]
sources: ["N013-volume-as-a-filter-for-false-breakouts", "R052-filters-for-confirming-breakouts"]
seed_id: breakout_volume_risk
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# Volume-Confirmed Breakouts: Stop at Invalidation Level

## Discovery Summary

N013-volume-as-a-filter-for-false-breakouts and R052-filters-for-confirming-breakouts combine into a single breakout validation rule: a breakout is tradeable only when volume expansion and confirmation filters align. This definition of a false breakout gives a concrete stop location — place the stop at the price level where the volume/confirmation thesis is invalidated, such as a close back inside the breakout range or below the breakout bar. The stop is therefore tied to the conditional logic of the entry, not just an arbitrary distance.

## Trading Implication

A trader should enter breakouts only when volume confirms and R052 filters are met, and if that confirmation fails, exit immediately or place an initial stop at the false-breakout invalidation level.

## Supporting Notes

- [[N013-volume-as-a-filter-for-false-breakouts]]
- [[R052-filters-for-confirming-breakouts]]

## Connection Type

**adds_condition** — Actionability score: 4/5
