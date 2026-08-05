---
type: insight
date: 2026-08-04
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
# Volume Distinguishes Breakaway Gaps From Exhaustion Gaps

## Discovery Summary

N150 and C328 identify gap types with opposing implications: breakaway gaps signal new trends (chase), exhaustion gaps signal trend endings (fade). R082 provides the missing filter — heavy volume validates breakouts. Applied to gaps: a gap accompanied by heavy volume is likely a breakaway gap (chase), while a gap on declining or average volume near trend exhaustion is more likely an exhaustion gap (fade). This volume condition, drawn from R082, converts the qualitative gap taxonomy into an actionable decision rule.

## Trading Implication

When a gap occurs, check volume immediately: a gap with surging volume (per R082) should be traded in the direction of the gap as a breakaway; a gap with weak or declining volume, especially after an extended trend, should be faded as a probable exhaustion gap.

## Supporting Notes

- [[N150-price-gaps-types]]
- [[R082-breakouts-must-be-accompanied-by-heavy-volume]]
- [[C328-gaps]]

## Connection Type

**creates_filter** — Actionability score: 4/5
