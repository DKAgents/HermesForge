---
type: insight
date: 2026-08-05
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

N150 and C328 classify gaps by their trend implications (breakaway=new trend, runaway=trend continuation, exhaustion=trend end), but neither specifies a validation mechanism. R082 supplies that mechanism: breakouts accompanied by heavy volume are valid signals. Combining these, a breakaway gap with surging volume (per R082) is a chase signal, while a gap occurring on declining or average volume — particularly after an extended move — is a candidate exhaustion gap to fade. The volume context transforms gap classification from a retroactive label into a prospective decision rule.

## Trading Implication

When a gap appears, check volume immediately: a gap accompanied by heavy volume surge should be chased as a breakaway or runaway signal; a gap on weak or average volume after a prolonged trend should be faded as a probable exhaustion gap, with a stop above the gap for shorts or below for longs.

## Supporting Notes

- [[N150-price-gaps-types]]
- [[R082-breakouts-must-be-accompanied-by-heavy-volume]]
- [[C328-gaps]]

## Connection Type

**creates_filter** — Actionability score: 4/5
