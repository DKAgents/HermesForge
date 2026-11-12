---
type: insight
date: 2026-11-11
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
# Volume confirms breakaway gaps, filters false signals

## Discovery Summary

N150-price-gaps-types and C328-gaps distinguish breakaway gaps as new-trend signals, but neither provides a validity filter. R082-breakouts-must-be-accompanied-by-heavy-volume supplies that missing condition: a breakout is only real when heavier trading activity occurs. Therefore, a gap acting as a breakout should be treated as a valid breakaway gap only if confirmed by a volume surge; otherwise it may be a common gap or false signal.

## Trading Implication

Do not chase a gap breakout unless volume is clearly elevated; require heavy volume to validate a breakaway gap, and otherwise treat the gap as likely to be filled or unreliable.

## Supporting Notes

- [[N150-price-gaps-types]]
- [[R082-breakouts-must-be-accompanied-by-heavy-volume]]
- [[C328-gaps]]

## Connection Type

**adds_condition** — Actionability score: 4/5
