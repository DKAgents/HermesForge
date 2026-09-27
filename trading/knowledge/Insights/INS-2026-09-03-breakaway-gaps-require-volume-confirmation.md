---
type: insight
date: 2026-09-03
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
# Breakaway Gaps Require Volume Confirmation

## Discovery Summary

N150 defines breakaway gaps as signals that start a new trend, while R082 states that all breakout points require heavy volume for the signal to be valid. Although the gap notes do not mention volume, applying the volume rule to breakaway gaps creates a filter: a gap must be accompanied by a volume surge to be treated as a genuine breakaway gap rather than a common gap. This condition is not explicit in the gap typology and improves signal reliability.

## Trading Implication

Only trade in the direction of a breakaway gap when it is confirmed by a clear surge in trading volume; if volume is absent, treat the gap as suspect and do not chase it.

## Supporting Notes

- [[N150-price-gaps-types]]
- [[R082-breakouts-must-be-accompanied-by-heavy-volume]]
- [[C328-gaps]]

## Connection Type

**adds_condition** — Actionability score: 4/5
