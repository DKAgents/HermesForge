---
type: insight
date: 2026-11-05
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
# Validate Breakaway Gaps with Heavy Volume

## Discovery Summary

N150 identifies breakaway gaps as signals of new trend starts, while R082 states all breakout points require heavy volume for validity. C328 confirms gaps indicate strength/weakness. Thus, a breakaway gap must occur on heavy volume to be a reliable trend-start signal; otherwise it is likely a common gap or a false signal.

## Trading Implication

When a gap forms, check accompanying volume. Only treat it as a breakaway gap (and therefore a trend-start signal) if volume is clearly above average; otherwise, treat it as a common gap and avoid chasing the move.

## Supporting Notes

- [[N150-price-gaps-types]]
- [[R082-breakouts-must-be-accompanied-by-heavy-volume]]
- [[C328-gaps]]

## Connection Type

**adds_condition** — Actionability score: 4/5
