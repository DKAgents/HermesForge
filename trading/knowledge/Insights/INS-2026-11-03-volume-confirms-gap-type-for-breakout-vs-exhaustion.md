---
type: insight
date: 2026-11-03
actionability: 4
connection_type: adds_condition
domains: [concepts, patterns, rules]
sources: ["N150-price-gaps-types", "R082-breakouts-must-be-accompanied-by-heavy-volume", "C328-gaps"]
seed_id: gap_continuation_volume
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# Volume Confirms Gap Type for Breakout vs Exhaustion

## Discovery Summary

The Price Gaps Types note distinguishes breakaway gaps (start of new trend), runaway gaps (middle of trend), and exhaustion gaps (end of trend). The R082 rule states that all pattern breakouts require heavy volume to be valid. Applying this rule to gap formations, a gap that occurs with high volume is more likely a genuine breakaway gap, while a gap on low volume may be a common or exhaustion gap, reducing its reliability as a trend signal.

## Trading Implication

When a gap occurs, compare its volume to recent averages. If volume is significantly above average, treat the gap as a breakaway and consider entering in the gap direction; if volume is light, avoid chasing and consider fading if the gap appears after an extended move.

## Supporting Notes

- [[N150-price-gaps-types]]
- [[R082-breakouts-must-be-accompanied-by-heavy-volume]]
- [[C328-gaps]]

## Connection Type

**adds_condition** — Actionability score: 4/5

## Related Notes
- [[N150-price-gaps-types|Price Gaps Types]]
