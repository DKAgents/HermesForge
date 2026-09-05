---
type: insight
date: 2026-09-05
actionability: 4
connection_type: creates_filter
domains: [concepts, patterns, rules]
sources: ["N150-price-gaps-types", "R082-breakouts-must-be-accompanied-by-heavy-volume", "C328-gaps"]
seed_id: gap_continuation_volume
tags: [insight, discovery, knowledge-evolution]
---

# Volume confirms breakaway gaps as valid breakouts

## Discovery Summary

R082 requires all price pattern breakouts to be validated by heavy volume. Applying this rule to gap types from N150 and C328, a breakaway gap—defined as signalling the start of a new trend—should exhibit a surge in volume to be considered a genuine breakout. This distinguishes breakaway gaps from common gaps (which lack volume confirmation) and helps identify when to chase a gap versus fade, directly addressing the seed question.

## Trading Implication

Only enter in the direction of a gap if it is accompanied by significantly heavy volume, confirming it as a breakaway gap; consider fading gaps that occur on light volume or after an extended trend with extreme volume (exhaustion gaps).

## Supporting Notes

- [[N150-price-gaps-types]]
- [[R082-breakouts-must-be-accompanied-by-heavy-volume]]
- [[C328-gaps]]

## Connection Type

**creates_filter** — Actionability score: 4/5
