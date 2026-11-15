---
type: insight
date: 2026-11-14
actionability: 4
connection_type: creates_filter
domains: [concepts, patterns, rules]
sources: ["N150-price-gaps-types", "R082-breakouts-must-be-accompanied-by-heavy-volume", "C328-gaps"]
seed_id: gap_continuation_volume
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# Volume filters gap type: chase breakaway, fade exhaustion

## Discovery Summary

C328-gaps and N150-price-gaps-types classify gaps but leave ambiguity about which gaps to trade. R082-breakouts-must-be-accompanied-by-heavy-volume supplies the missing filter: a breakaway gap at a pattern breakout is valid only with heavy volume, while a late-trend exhaustion gap should be treated as a fade/reversal signal rather than a breakout continuation. Thus volume confirms the gap type and resolves the chase-vs-fade decision.

## Trading Implication

Chase a gap only when it occurs at a pattern breakout with a clear volume surge; if a gap appears late in an established trend without such breakout context/volume, treat it as a potential exhaustion gap and avoid chasing or consider fading.

## Supporting Notes

- [[N150-price-gaps-types]]
- [[R082-breakouts-must-be-accompanied-by-heavy-volume]]
- [[C328-gaps]]

## Connection Type

**creates_filter** — Actionability score: 4/5
