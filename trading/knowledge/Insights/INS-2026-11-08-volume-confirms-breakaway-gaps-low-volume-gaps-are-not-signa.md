---
type: insight
date: 2026-11-08
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
# Volume Confirms Breakaway Gaps; Low-Volume Gaps Are Not Signals

## Discovery Summary

R082-breakouts-must-be-accompanied-by-heavy-volume provides the confirmation condition missing from N150-price-gaps-types: a breakaway gap should be treated as a genuine breakout signal only if volume expands on the gap. A gap without heavy volume is better classified as a common gap and should not be chased. N150's exhaustion gap also shows that volume alone is not enough; when the gap occurs late in a trend it may be a final fade signal, so context and volume must be combined.

## Trading Implication

Before trading a gap as a breakout/continuation signal, require a volume surge relative to the prior consolidation; if volume is absent, ignore or fade the gap. For gaps after extended trends, treat even high-volume gaps as potential exhaustion and avoid chasing.

## Supporting Notes

- [[N150-price-gaps-types]]
- [[R082-breakouts-must-be-accompanied-by-heavy-volume]]
- [[C328-gaps]]

## Connection Type

**creates_filter** — Actionability score: 4/5
