---
type: insight
date: 2026-10-15
actionability: 3
connection_type: adds_condition
domains: [breakout patterns, indicators, risk management, trading rules]
sources: ["N013-volume-as-a-filter-for-false-breakouts", "R052-filters-for-confirming-breakouts"]
seed_id: breakout_volume_risk
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# Volume filter confirms breakouts and guides false-breakout stops

## Discovery Summary

N013's volume-as-a-filter-for-false-breakouts adds a specific condition to R052's generic filters-for-confirming-breakouts rule. A breakout is only valid if it occurs on above-average volume; otherwise it is likely false. This distinction lets a trader place stops beyond the false-breakout range instead of treating the breakout as a real reversal.

## Trading Implication

Before acting on a breakout, require a volume surge as a confirming filter; if volume is absent, treat the breakout as false and place the stop at the far side of the failed breakout zone or stand aside.

## Supporting Notes

- [[N013-volume-as-a-filter-for-false-breakouts]]
- [[R052-filters-for-confirming-breakouts]]

## Connection Type

**adds_condition** — Actionability score: 3/5
