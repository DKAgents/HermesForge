---
type: insight
date: 2026-11-19
actionability: 4
connection_type: adds_condition
domains: [concepts, patterns, rules]
sources: ["N150-price-gaps-types", "R082-breakouts-must-be-accompanied-by-heavy-volume", "C328-gaps"]
seed_id: gap_continuation_volume
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# Volume confirms breakaway gaps; without it, don't chase

## Discovery Summary

N150-price-gaps-types defines breakaway gaps as signals of a new trend, while R082-breakouts-must-be-accompanied-by-heavy-volume requires heavy volume to validate any real breakout. Applying this rule to gap signals creates a filter: a breakaway gap should only be treated as a valid trend-start signal if it occurs at a pattern resolution with a volume surge. Without that confirmation, the gap may be a common gap or a false breakout rather than a reason to chase. This gives a concrete way to reconcile C328-gaps' directional bias with Murphy's volume requirement.

## Trading Implication

When a breakaway gap appears, check volume before entering; only chase if the gap is accompanied by a clear surge in trading activity, otherwise wait for confirmation or treat the gap as suspect.

## Supporting Notes

- [[N150-price-gaps-types]]
- [[R082-breakouts-must-be-accompanied-by-heavy-volume]]
- [[C328-gaps]]

## Connection Type

**adds_condition** — Actionability score: 4/5
