---
type: insight
date: 2026-08-14
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

N150 and C328 establish that gap types have directionally opposite implications: breakaway/runaway gaps signal trend continuation (chase), while exhaustion gaps signal trend reversal (fade). R082 provides the missing discriminator — volume surge at a breakaway gap validates it as a real signal, while an exhaustion gap typically occurs on diminishing or climactic volume. By combining gap classification with the volume confirmation rule from R082, a trader can distinguish chaseable gaps from fadeable ones with a concrete, observable criterion.

## Trading Implication

Chase a gap only if it occurs with a heavy volume surge consistent with R082's breakout confirmation standard; if a gap appears after an extended trend with climactic or fading volume, treat it as an exhaustion gap and fade or exit rather than enter in the trend direction.

## Supporting Notes

- [[N150-price-gaps-types]]
- [[R082-breakouts-must-be-accompanied-by-heavy-volume]]
- [[C328-gaps]]

## Connection Type

**creates_filter** — Actionability score: 4/5
