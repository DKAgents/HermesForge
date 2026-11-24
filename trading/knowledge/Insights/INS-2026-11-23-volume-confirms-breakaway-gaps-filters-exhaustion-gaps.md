---
type: insight
date: 2026-11-23
actionability: 3
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
# Volume Confirms Breakaway Gaps, Filters Exhaustion Gaps

## Discovery Summary

N150-price-gaps-types and C328-gaps classify breakaway gaps as trend starts and exhaustion gaps as trend ends, but they do not specify how to validate them. R082-breakouts-must-be-accompanied-by-heavy-volume supplies the missing filter: a gap acting as a breakout is valid only if accompanied by heavier trading activity. Applying this rule lets a trader distinguish a high-volume breakaway gap from a low-volume common or exhaustion gap.

## Trading Implication

Do not chase a gap unless the gap bar shows a clear volume surge; if volume is light, treat the gap as common or exhaustion and avoid fading or entering in the gap direction without further confirmation.

## Supporting Notes

- [[N150-price-gaps-types]]
- [[R082-breakouts-must-be-accompanied-by-heavy-volume]]
- [[C328-gaps]]

## Connection Type

**creates_filter** — Actionability score: 3/5
