---
type: insight
date: 2026-11-06
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
# Volume and Trend Location Classify Gap as Chase or Fade

## Discovery Summary

N150-price-gaps-types defines breakaway, runaway, and exhaustion gaps by trend position, while R082-breakouts-must-be-accompanied-by-heavy-volume requires volume to confirm a real breakout. C328-gaps notes that up/down gaps signal strength/weakness but does not distinguish exhaustion gaps. Combining these, the volume rule should only validate breakaway/runaway gaps; a gap after an extended trend should be classified as exhaustion and faded rather than chased, even if it resembles a breakout.

## Trading Implication

Before acting on a gap, determine its trend location: require a volume surge for early/mid-trend breakaway/runaway gaps, and treat late-trend gaps as exhaustion signals to fade instead of chase.

## Supporting Notes

- [[N150-price-gaps-types]]
- [[R082-breakouts-must-be-accompanied-by-heavy-volume]]
- [[C328-gaps]]

## Connection Type

**creates_filter** — Actionability score: 4/5
