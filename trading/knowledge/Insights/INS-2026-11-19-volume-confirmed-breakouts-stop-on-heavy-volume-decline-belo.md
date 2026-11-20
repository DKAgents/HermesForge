---
type: insight
date: 2026-11-19
actionability: 4
connection_type: reveals_sequence
domains: [indicators, patterns, risk_guidelines, rules]
sources: ["N013-volume-as-a-filter-for-false-breakouts", "R052-filters-for-confirming-breakouts", "N028-bull-trap-false-upside-breakout"]
seed_id: breakout_volume_risk
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# Volume-confirmed breakouts: stop on heavy-volume decline below breakout

## Discovery Summary

R052 provides pre-entry confirmation filters for breakouts, but N013 and N028 identify the false-breakout signature as a sequence: a light-volume upside breakout followed by a heavy-volume decline. That sequence transforms the breakout level into a stop trigger: if price breaks back below the prior resistance after a light-volume breakout, the heavy-volume decline confirms a bull trap and requires exit. This connects breakout rules, volume indicators, and stop placement into a single exit rule.

## Trading Implication

Before entering, apply R052 filters and require heavy volume on the breakout; once long, place a stop just below the breakout level and exit if price closes back below it on heavy volume following a light-volume breakout. A light-volume dip below the level should not be treated as the same false-breakout trigger.

## Supporting Notes

- [[N013-volume-as-a-filter-for-false-breakouts]]
- [[R052-filters-for-confirming-breakouts]]
- [[N028-bull-trap-false-upside-breakout]]

## Connection Type

**reveals_sequence** — Actionability score: 4/5
