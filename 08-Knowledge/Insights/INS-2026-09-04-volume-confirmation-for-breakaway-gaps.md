---
type: insight
date: 2026-09-04
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
# Volume Confirmation for Breakaway Gaps

## Discovery Summary

Rule R082 requires heavy volume at the breakout point of a price pattern to validate the signal. Since a breakaway gap (N150, C328) is a breakout from a congestion area marking the start of a new trend, it should also be accompanied by a surge in volume to be considered genuine. Without heavy volume, a gap that appears to be breakaway may actually be a common gap and prone to failure.

## Trading Implication

Before chasing a breakaway gap, confirm a volume spike; if volume is weak, fade the gap instead, treating it as a common gap with no directional follow-through.

## Supporting Notes

- [[N150-price-gaps-types]]
- [[R082-breakouts-must-be-accompanied-by-heavy-volume]]
- [[C328-gaps]]

## Connection Type

**creates_filter** — Actionability score: 4/5
