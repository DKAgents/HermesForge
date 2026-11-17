---
type: insight
date: 2026-11-16
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
# Volume Confirms Gap Type Before Chasing Breakouts

## Discovery Summary

N150-price-gaps-types distinguishes common, breakaway, runaway, and exhaustion gaps, while C328-gaps notes that up gaps show strength and down gaps show weakness. R082-breakouts-must-be-accompanied-by-heavy-volume says pattern breakouts are valid only with heavier volume. Applying this to gaps means a gap should be treated as a tradable breakaway/runaway signal only if volume expands; low-volume gaps are likely common and should not be chased.

## Trading Implication

Before acting on a gap, check volume: enter on breakaway/runaway gaps with a volume surge, and ignore or fade low-volume gaps that are likely to be filled.

## Supporting Notes

- [[N150-price-gaps-types]]
- [[R082-breakouts-must-be-accompanied-by-heavy-volume]]
- [[C328-gaps]]

## Connection Type

**adds_condition** — Actionability score: 4/5
