---
type: insight
date: 2026-11-18
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
# Volume-confirm gaps to distinguish breakaway from exhaustion

## Discovery Summary

N150-price-gaps-types identifies breakaway and runaway gaps as trend signals, while exhaustion gaps mark reversals. C328-gaps adds that up gaps show strength and down gaps show weakness. However, R082-breakouts-must-be-accompanied-by-heavy-volume states every breakout must have heavier trading activity to be valid; applying this rule to gaps creates a filter: heavy-volume gaps are more likely genuine breakaways/continuations, while low-volume gaps are suspect and may be common or exhaustion gaps.

## Trading Implication

Chase a gap only if it is accompanied by a clear volume surge in the direction of the gap; treat weak-volume gaps as likely common/exhaustion gaps and avoid chasing, or consider fading them.

## Supporting Notes

- [[N150-price-gaps-types]]
- [[R082-breakouts-must-be-accompanied-by-heavy-volume]]
- [[C328-gaps]]

## Connection Type

**creates_filter** — Actionability score: 4/5
