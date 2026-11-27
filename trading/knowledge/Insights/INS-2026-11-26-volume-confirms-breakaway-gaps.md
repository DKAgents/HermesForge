---
type: insight
date: 2026-11-26
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
# Volume Confirms Breakaway Gaps

## Discovery Summary

N150-price-gaps-types and C328-gaps classify gap types (breakaway, runaway, exhaustion) but do not specify validation. R082-breakouts-must-be-accompanied-by-heavy-volume states that any pattern breakout must occur on heavy volume. A gap is a breakout from prior price action, so volume must confirm the gap type: a breakaway gap on low volume is likely a common gap, while a runaway gap on high volume confirms trend continuation.

## Trading Implication

Before trading a gap, check volume: if volume is not significantly above average, treat it as a common gap and avoid chasing; if volume surges with the gap, treat it as a genuine breakaway or runaway signal and trade in the gap direction.

## Supporting Notes

- [[N150-price-gaps-types]]
- [[R082-breakouts-must-be-accompanied-by-heavy-volume]]
- [[C328-gaps]]

## Connection Type

**adds_condition** — Actionability score: 4/5
