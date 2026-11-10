---
type: insight
date: 2026-11-09
actionability: 4
connection_type: resolves_conflict
domains: [concepts, patterns, rules]
sources: ["N150-price-gaps-types", "R082-breakouts-must-be-accompanied-by-heavy-volume", "C328-gaps"]
seed_id: gap_continuation_volume
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# Volume validates gap type: chase breakaway, fade exhaustion

## Discovery Summary

R082-breakouts-must-be-accompanied-by-heavy-volume states that a breakout signal is only valid if accompanied by heavier trading activity. N150-price-gaps-types and C328-gaps define breakaway, runaway, and exhaustion gaps with opposite trading implications. Combining these, a gap's type can be disambiguated by volume: heavy volume confirms a breakaway/runaway gap worth chasing, while a low-volume gap at trend extremes is more likely an exhaustion gap to fade. This adds a concrete filter to the otherwise ambiguous gap-type classification.

## Trading Implication

When a gap appears, check the volume surge before acting: trade in the gap direction only if volume expands; if volume is light, treat it as a potential exhaustion/common gap and avoid chasing or consider fading.

## Supporting Notes

- [[N150-price-gaps-types]]
- [[R082-breakouts-must-be-accompanied-by-heavy-volume]]
- [[C328-gaps]]

## Connection Type

**resolves_conflict** — Actionability score: 4/5
