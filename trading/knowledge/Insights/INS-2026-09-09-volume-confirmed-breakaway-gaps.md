---
type: insight
date: 2026-09-09
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
# Volume-Confirmed Breakaway Gaps

## Discovery Summary

Rule R082 mandates that all price pattern breakouts need heavy volume to be valid. Breakaway gaps (described in N150 and C328) are breakouts from a trading range that signal a new trend. Applying the volume rule to gaps: a breakaway gap is only a reliable chase signal if it occurs on a volume surge, filtering out low-conviction moves.

## Trading Implication

Only chase a breakaway gap if it is accompanied by significantly above-average volume; if volume is lacking, fade the gap or wait for confirmation instead of assuming a trend start.

## Supporting Notes

- [[N150-price-gaps-types]]
- [[R082-breakouts-must-be-accompanied-by-heavy-volume]]
- [[C328-gaps]]

## Connection Type

**creates_filter** — Actionability score: 4/5
