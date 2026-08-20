---
type: insight
date: 2026-08-19
actionability: 4
connection_type: adds_condition
domains: [concepts, patterns, rules]
sources: ["N150-price-gaps-types", "R082-breakouts-must-be-accompanied-by-heavy-volume", "C328-gaps"]
seed_id: gap_continuation_volume
tags: [insight, discovery, knowledge-evolution]
topic: knowledge
confidence: high
has_quotes: false
source: unknown
---
# Volume Validates Gap Type: Chase vs Fade Decision Rule

## Discovery Summary

N150 and C328 establish that gap types carry opposing implications — breakaway and runaway gaps signal continuation (chase), while exhaustion gaps signal reversal (fade). R082 adds a critical filter: breakout validity requires heavy volume. Combining these, a gap should only be chased if accompanied by a volume surge (confirming breakaway or runaway character), while a gap on declining or average volume is more likely an exhaustion gap and a fade candidate. The island reversal pattern in N150 provides a specific structure where a breakaway gap following an exhaustion gap, with volume confirmation on the second gap, creates a high-confidence fade-turned-chase setup.

## Trading Implication

A trader should only chase a gap if volume is significantly above average (confirming breakaway/runaway type per R082); gaps on light volume should be faded as probable exhaustion gaps, with the island reversal structure (exhaustion gap + opposite breakaway gap with heavy volume) as the highest-conviction fade-to-reversal entry signal.

## Supporting Notes

- [[N150-price-gaps-types]]
- [[R082-breakouts-must-be-accompanied-by-heavy-volume]]
- [[C328-gaps]]

## Connection Type

**adds_condition** — Actionability score: 4/5
