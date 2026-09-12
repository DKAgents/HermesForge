---
type: insight
date: 2026-09-12
actionability: 4
connection_type: adds_condition
domains: [concepts, patterns, rules]
sources: ["N150-price-gaps-types", "R082-breakouts-must-be-accompanied-by-heavy-volume", "C328-gaps"]
seed_id: gap_continuation_volume
tags: [insight, discovery, knowledge-evolution]
---

# Volume confirms gap type at breakout points

## Discovery Summary

Rule R082 establishes that valid breakouts require heavy volume, while the gap typology in N150 and C328 distinguishes breakaway gaps from other gap types. The non-obvious connection is that volume can differentiate a true breakaway gap (valid breakout with trend initiation) from a common or exhaustion gap at pattern boundaries. An island reversal explicitly combines an exhaustion gap followed by a breakaway gap in the opposite direction—applying the volume rule to both gaps provides dual confirmation: the exhaustion gap should occur on lighter or climactic volume, while the subsequent breakaway gap must show heavy volume to validate the reversal signal.

## Trading Implication

Before treating a gap as a breakaway signal, confirm it coincides with heavy volume relative to the pattern's formation; if a gap at a pattern boundary lacks volume surge, treat it as a common gap and fade the move rather than chase it.

## Supporting Notes

- [[N150-price-gaps-types]]
- [[R082-breakouts-must-be-accompanied-by-heavy-volume]]
- [[C328-gaps]]

## Connection Type

**adds_condition** — Actionability score: 4/5
