---
type: insight
date: 2026-08-28
actionability: 4
connection_type: creates_filter
domains: [concepts, patterns, rules]
sources: ["N150-price-gaps-types", "R082-breakouts-must-be-accompanied-by-heavy-volume", "C328-gaps"]
seed_id: gap_continuation_volume
tags: [insight, discovery, knowledge-evolution]
topic: knowledge
confidence: high
has_quotes: false
source: unknown
---
# Volume Confirms Breakaway Gap Validity

## Discovery Summary

R082 requires heavy volume at pattern breakouts for signal validity. Extending this to gap types (N150, C328), a breakaway gap—which signals the start of a new trend—should also require a volume surge to be considered reliable. Conversely, a gap occurring without heavy volume may be a common gap or a false breakaway signal, helping traders avoid failed moves.

## Trading Implication

Only chase a gap as a trend start (breakaway) if it coincides with a clear pickup in volume; fade or ignore gaps that lack volume confirmation.

## Supporting Notes

- [[N150-price-gaps-types]]
- [[R082-breakouts-must-be-accompanied-by-heavy-volume]]
- [[C328-gaps]]

## Connection Type

**creates_filter** — Actionability score: 4/5
