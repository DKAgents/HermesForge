---
type: insight
date: 2026-08-09
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
# Volume Confirms Gap Type: Chase vs Fade Decision Rule

## Discovery Summary

N150 and C328 identify gap types with opposite implications (breakaway = chase, exhaustion = fade), but neither provides a reliable in-the-moment classifier. R082 supplies the missing discriminator: breakaway and runaway gaps should be accompanied by heavy volume (confirming the move), while exhaustion gaps — occurring at trend extremes — are more likely to appear on declining or average volume before the reversal. This volume filter operationalizes the otherwise ambiguous gap-type identification problem.

## Trading Implication

When a gap appears, check volume immediately: a gap on surging volume signals a breakaway or runaway gap (chase/hold), while a gap on average or declining volume near a trend extreme signals an exhaustion gap (fade or tighten stops). Only take gap breakouts when volume confirms per R082.

## Supporting Notes

- [[N150-price-gaps-types]]
- [[R082-breakouts-must-be-accompanied-by-heavy-volume]]
- [[C328-gaps]]

## Connection Type

**creates_filter** — Actionability score: 4/5
