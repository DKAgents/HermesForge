---
type: insight
date: 2026-11-15
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
# Volume confirms breakaway gaps and island reversals

## Discovery Summary

N150 price-gaps-types defines breakaway gaps as new-trend signals and island reversals as exhaustion plus opposite breakaway gaps. R082-breakouts-must-be-accompanied-by-heavy-volume says any real breakout must occur on heavier volume. Applying R082 to N150 means a breakaway gap — including the second gap of an island reversal — is only a valid breakout if volume expands on that gap; otherwise it may be a common gap or false signal.

## Trading Implication

Before chasing a gap after a consolidation or reversal pattern, require volume on the gap bar to be clearly above recent average; if volume is missing, do not treat the gap as a trend-changing breakaway.

## Supporting Notes

- [[N150-price-gaps-types]]
- [[R082-breakouts-must-be-accompanied-by-heavy-volume]]
- [[C328-gaps]]

## Connection Type

**adds_condition** — Actionability score: 4/5
