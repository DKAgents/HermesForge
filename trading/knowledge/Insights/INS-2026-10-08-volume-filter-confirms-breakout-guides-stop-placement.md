---
type: insight
date: 2026-10-08
actionability: 4
connection_type: confirms_risk_rule
domains: [indicators, risk_guidelines, rules]
sources: ["N013-volume-as-a-filter-for-false-breakouts", "R052-filters-for-confirming-breakouts"]
seed_id: breakout_volume_risk
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# Volume filter confirms breakout, guides stop placement

## Discovery Summary

N013-volume-as-a-filter-for-false-breakouts identifies low volume as a sign of false breakouts, while R052-filters-for-confirming-breakouts lists criteria for valid breakouts. The non-obvious insight is to use volume as a gate: if breakout volume is insufficient (per N013), treat it as false and apply a tighter stop (e.g., just below the breakout level) as a risk management rule derived from combining both notes.

## Trading Implication

Traders should require volume confirmation before acting on a breakout per R052, and for low-volume breakouts, set stop-loss orders extremely close to the breakout boundary to limit false breakout losses.

## Supporting Notes

- [[N013-volume-as-a-filter-for-false-breakouts]]
- [[R052-filters-for-confirming-breakouts]]

## Connection Type

**confirms_risk_rule** — Actionability score: 4/5
