---
type: insight
date: 2026-08-31
actionability: 4
connection_type: creates_filter
domains: [concepts, patterns, rules]
sources: ["N150-price-gaps-types", "R082-breakouts-must-be-accompanied-by-heavy-volume", "C328-gaps"]
seed_id: gap_continuation_volume
tags: [insight, discovery, knowledge-evolution]
---

# Volume confirms gap type, not just breakout validity

## Discovery Summary

R082 states breakouts must be accompanied by heavy volume for validity, while N150 and C328 categorize gaps into common, breakaway, runaway, and exhaustion types. Applying the volume rule specifically to gap analysis creates a filter: breakaway gaps with heavy volume confirm new trend initiation, while gaps without volume surge suggest common gaps likely to fill. Runaway gaps occur mid-trend where volume may already be elevated, but exhaustion gaps accompanied by unusually heavy volume followed by an opposing breakaway gap form island reversals (N150).

## Trading Implication

Trade breakaway gaps only when accompanied by a clear volume surge relative to prior sessions; fade gaps that occur on average or declining volume as they are likely common gaps that will fill.

## Supporting Notes

- [[N150-price-gaps-types]]
- [[R082-breakouts-must-be-accompanied-by-heavy-volume]]
- [[C328-gaps]]

## Connection Type

**creates_filter** — Actionability score: 4/5
