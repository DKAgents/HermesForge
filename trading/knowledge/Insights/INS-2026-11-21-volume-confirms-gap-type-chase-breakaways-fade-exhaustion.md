---
type: insight
date: 2026-11-21
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
# Volume confirms gap type: chase breakaways, fade exhaustion

## Discovery Summary

N150-price-gaps-types distinguishes breakaway, runaway, and exhaustion gaps but gives no volume criterion, while R082-breakouts-must-be-accompanied-by-heavy-volume states that real breakouts require heavier trading activity. Applying R082 to C328-gaps means volume can filter which gap type is occurring: a high-volume gap after consolidation is a valid breakaway to chase, while a gap late in a trend on volume may be exhaustion and should be faded. A low-volume gap is likely a common gap and should not be traded as a breakout.

## Trading Implication

Before acting on any gap, check volume: chase only gaps accompanied by a clear volume surge; fade or ignore gaps that occur on low volume or after an extended trend.

## Supporting Notes

- [[N150-price-gaps-types]]
- [[R082-breakouts-must-be-accompanied-by-heavy-volume]]
- [[C328-gaps]]

## Connection Type

**creates_filter** — Actionability score: 4/5
