---
type: insight
date: 2026-09-15
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
# Gap Breakouts Need Volume Confirmation

## Discovery Summary

C328-gaps and N150-price-gaps-types identify breakaway gaps as initial trend signals, but R082-breakouts-must-be-accompanied-by-heavy-volume adds a critical condition: the gap alone is not enough—it must be accompanied by heavier trading volume to be a valid breakout. Without volume, a gap may be a common gap or a false breakout, so traders should wait for both price gap and volume surge before acting.

## Trading Implication

When a breakaway gap occurs, check volume; only enter if volume is significantly above recent average. If volume is low, treat the gap as suspect and avoid chasing until volume confirms.

## Supporting Notes

- [[N150-price-gaps-types]]
- [[R082-breakouts-must-be-accompanied-by-heavy-volume]]
- [[C328-gaps]]

## Connection Type

**adds_condition** — Actionability score: 4/5
