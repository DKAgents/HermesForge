---
type: insight
date: 2026-08-07
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

N150 identifies four gap types with opposing implications (breakaway/runaway = chase; exhaustion = fade), while R082 establishes that valid breakouts require heavy volume confirmation. C328 reinforces that gap direction signals strength or weakness. Combining these: a breakaway or runaway gap accompanied by heavy volume (per R082) is a valid chase signal, whereas a gap on diminishing or average volume — especially after an extended trend — should be treated as a potential exhaustion gap to fade.

## Trading Implication

Before entering on a gap, measure volume: if the gap occurs with a volume surge relative to recent average, treat it as a breakaway or runaway and trade in the direction; if volume is light or declining after a prolonged trend move, classify it as an exhaustion gap and look to fade or exit existing positions.

## Supporting Notes

- [[N150-price-gaps-types]]
- [[R082-breakouts-must-be-accompanied-by-heavy-volume]]
- [[C328-gaps]]

## Connection Type

**creates_filter** — Actionability score: 4/5
