---
type: insight
date: 2026-10-19
actionability: 4
connection_type: adds_condition
domains: [breakout patterns, indicators, risk guidelines, trading rules]
sources: ["N013-volume-as-a-filter-for-false-breakouts", "R052-filters-for-confirming-breakouts"]
seed_id: breakout_volume_risk
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# Volume-confirmed breakouts set stops; low-volume false breakouts invalidate

## Discovery Summary

N013-volume-as-a-filter-for-false-breakouts supplies the missing volume condition in R052-filters-for-confirming-breakouts: a breakout is only reliable when volume supports it. When volume fails to confirm, the move is classified as a false breakout, and this classification dictates stop placement. Stops should be placed at or inside the breakout boundary rather than trailing the false move, because the breakout pattern has been invalidated.

## Trading Implication

Require a volume threshold before taking a breakout; if the breakout occurs on low volume, place a stop at the prior range boundary or avoid the trade entirely.

## Supporting Notes

- [[N013-volume-as-a-filter-for-false-breakouts]]
- [[R052-filters-for-confirming-breakouts]]

## Connection Type

**adds_condition** — Actionability score: 4/5
