---
type: insight
date: 2026-08-06
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

N150 identifies four gap types with opposing implications (breakaway gaps signal trend initiation to chase; exhaustion gaps signal trend termination to fade), while R082 establishes that valid breakouts require heavy volume. C328 confirms gaps represent price voids showing directional strength or weakness. Combining these: volume magnitude at the gap distinguishes breakaway gaps (high volume surge = chase) from exhaustion gaps (climactic, often highest volume of the move = fade), creating a volume-based filter to differentiate between gap types in real-time.

## Trading Implication

When a gap occurs, measure volume relative to recent average: if volume is surging on a gap from a consolidation base, treat it as a breakaway gap and trade in gap direction; if volume is climactically extreme after an extended trend (especially if followed by a reversal bar), treat it as an exhaustion gap and fade or avoid chasing.

## Supporting Notes

- [[N150-price-gaps-types]]
- [[R082-breakouts-must-be-accompanied-by-heavy-volume]]
- [[C328-gaps]]

## Connection Type

**creates_filter** — Actionability score: 4/5
