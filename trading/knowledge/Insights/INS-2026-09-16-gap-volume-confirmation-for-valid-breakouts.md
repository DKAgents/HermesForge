---
type: insight
date: 2026-09-16
actionability: 4
connection_type: adds_condition
domains: [concepts, patterns, rules]
sources: ["N150-price-gaps-types", "R082-breakouts-must-be-accompanied-by-heavy-volume", "C328-gaps"]
seed_id: gap_continuation_volume
tags: [insight, discovery, knowledge-evolution]
topic: knowledge
confidence: high
has_quotes: false
source: unknown
---
# Gap volume confirmation for valid breakouts

## Discovery Summary

Murphy's rule (R082) states breakouts must be accompanied by heavy volume, but gap notes (C328, N150) describe breakaway gaps as signaling new trends but do not explicitly require volume. Connecting them: a breakaway gap at a pattern breakout is only valid if confirmed by a volume surge, otherwise it risks being a common or exhaustion gap. This filters false breakouts and distinguishes breakaway from exhaustion gaps.

## Trading Implication

When a breakaway gap forms at a pattern resolution, check for a concurrent volume spike; if volume is low or declining, treat the gap as a potential exhaustion gap and avoid entering or consider fading the move.

## Supporting Notes

- [[N150-price-gaps-types]]
- [[R082-breakouts-must-be-accompanied-by-heavy-volume]]
- [[C328-gaps]]

## Connection Type

**adds_condition** — Actionability score: 4/5
