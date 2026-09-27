---
type: insight
date: 2026-08-30
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
# Volume validates gap type and breakout reliability

## Discovery Summary

R082 establishes that all valid breakouts require heavy volume. When applied to gap analysis from C328 and N150, this rule distinguishes between gap types: breakaway gaps should show a volume surge (confirming the breakout), while exhaustion gaps may lack volume follow-through. A breakaway gap without heavy volume signals a false breakout, and a gap appearing mid-trend with declining volume suggests it may be exhaustion rather than a valid runaway/measuring gap.

## Trading Implication

Before trading a gap as a breakaway or continuation signal, verify volume spiked on the gap day. If a gap occurs without heavy volume, fade it or wait for volume confirmation rather than chasing the move.

## Supporting Notes

- [[N150-price-gaps-types]]
- [[R082-breakouts-must-be-accompanied-by-heavy-volume]]
- [[C328-gaps]]

## Connection Type

**adds_condition** — Actionability score: 4/5
