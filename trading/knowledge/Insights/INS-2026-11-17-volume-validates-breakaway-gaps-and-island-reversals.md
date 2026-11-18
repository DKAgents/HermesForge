---
type: insight
date: 2026-11-17
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
# Volume validates breakaway gaps and island reversals

## Discovery Summary

N150-price-gaps-types identifies breakaway gaps as start-of-trend signals, but lacks a validity condition. R082-breakouts-must-be-accompanied-by-heavy-volume supplies that missing filter: if a breakaway gap is a true pattern resolution, it should show heavier trading activity. Without a volume surge, the gap is more likely a common gap or false breakout. The same logic applies to island reversals, where the second breakaway gap in the opposite direction needs volume confirmation.

## Trading Implication

Do not chase an apparent breakaway gap unless volume expands on the gap bar; wait for a volume-backed reversal gap before acting on an island reversal.

## Supporting Notes

- [[N150-price-gaps-types]]
- [[R082-breakouts-must-be-accompanied-by-heavy-volume]]
- [[C328-gaps]]

## Connection Type

**creates_filter** — Actionability score: 4/5
