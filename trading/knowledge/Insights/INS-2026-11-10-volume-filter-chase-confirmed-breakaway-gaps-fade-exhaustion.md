---
type: insight
date: 2026-11-10
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
# Volume Filter: Chase Confirmed Breakaway Gaps, Fade Exhaustion

## Discovery Summary

N150-price-gaps-types and C328-gaps classify gaps by trend position, but R082-breakouts-must-be-accompanied-by-heavy-volume supplies the missing validation: a gap acting as a breakout must show a volume surge. This creates a filter for gap trading — only breakaway/runaway gaps with heavy volume are reliable continuation signals, while gaps without volume confirmation should not be chased. Exhaustion gaps, as end-of-trend signals, are fade candidates rather than breakout entries.

## Trading Implication

Before acting on a gap, check volume: chase breakaway/runaway gaps only when volume expands at the gap, and treat exhaustion gaps near trend extremes as reversal/fade signals rather than continuation breakouts.

## Supporting Notes

- [[N150-price-gaps-types]]
- [[R082-breakouts-must-be-accompanied-by-heavy-volume]]
- [[C328-gaps]]

## Connection Type

**creates_filter** — Actionability score: 4/5
