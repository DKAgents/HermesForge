---
type: insight
date: 2026-09-08
actionability: 4
connection_type: creates_filter
domains: [concepts, patterns, rules]
sources: ["N150-price-gaps-types", "R082-breakouts-must-be-accompanied-by-heavy-volume", "C328-gaps"]
seed_id: gap_continuation_volume
tags: [insight, discovery, knowledge-evolution]
---

# Volume Confirms Breakaway Gap Validity

## Discovery Summary

N150 explains that breakaway gaps signal the start of a new trend, while C328 defines gaps without mentioning volume. R082 states that all breakout signals require heavy volume to be valid. Combining these, a breakaway gap should be treated as a valid breakout only when accompanied by a volume surge; low-volume gaps are more likely common gaps, which have no trend implications.

## Trading Implication

Before chasing a breakaway gap, verify it occurs on significantly heavier volume than recent sessions. A breakaway gap without a volume surge should be treated as a common gap and faded rather than chased.

## Supporting Notes

- [[N150-price-gaps-types]]
- [[R082-breakouts-must-be-accompanied-by-heavy-volume]]
- [[C328-gaps]]

## Connection Type

**creates_filter** — Actionability score: 4/5
