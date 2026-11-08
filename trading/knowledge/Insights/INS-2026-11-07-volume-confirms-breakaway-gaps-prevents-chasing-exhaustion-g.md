---
type: insight
date: 2026-11-07
actionability: 4
connection_type: resolves_conflict
domains: [concepts, patterns, rules]
sources: ["N150-price-gaps-types", "R082-breakouts-must-be-accompanied-by-heavy-volume", "C328-gaps"]
seed_id: gap_continuation_volume
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# Volume confirms breakaway gaps, prevents chasing exhaustion gaps

## Discovery Summary

C328-gaps says an up gap is usually a sign of strength, but N150-price-gaps-types warns that exhaustion gaps signal trend end, so a gap alone is ambiguous. R082-breakouts-must-be-accompanied-by-heavy-volume supplies the missing filter: a real breakout, including a breakaway gap, must be confirmed by heavy volume. Therefore, a gap breaking out of a consolidation on a volume surge is a valid breakaway signal, while a gap without such volume confirmation should not be chased as a trend-starting move.

## Trading Implication

When a gap appears, immediately check volume: if it emerges from a consolidation on a volume surge, trade in the gap direction; if volume is light or the move is extended, treat it as common/exhaustion and avoid chasing it.

## Supporting Notes

- [[N150-price-gaps-types]]
- [[R082-breakouts-must-be-accompanied-by-heavy-volume]]
- [[C328-gaps]]

## Connection Type

**resolves_conflict** — Actionability score: 4/5
