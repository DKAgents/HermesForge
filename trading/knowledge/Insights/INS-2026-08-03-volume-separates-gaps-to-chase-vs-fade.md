---
type: insight
date: 2026-08-03
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
# Volume Separates Gaps to Chase vs Fade

## Discovery Summary

N150 identifies four gap types with directionally opposite implications: breakaway gaps signal trend starts (chase), runaway gaps confirm trend continuation (chase), and exhaustion gaps signal trend endings (fade). C328 confirms gaps indicate strength or weakness. R082 establishes that valid breakouts require heavy volume — this volume rule, applied to gap classification, provides the critical filter: breakaway and runaway gaps should occur on surging volume (valid signal to chase), while exhaustion gaps characteristically occur on high volume that then fails to follow through, providing a real-time fade signal when subsequent price action stalls.

## Trading Implication

On any gap open, require immediate confirmation of heavy volume before chasing; if volume spikes but price fails to extend beyond the gap in the gap's direction within the first 30-60 minutes, treat as an exhaustion gap and fade the move rather than chase it.

## Supporting Notes

- [[N150-price-gaps-types]]
- [[R082-breakouts-must-be-accompanied-by-heavy-volume]]
- [[C328-gaps]]

## Connection Type

**creates_filter** — Actionability score: 4/5

## Related Notes
- [[N161-runaway-gaps|Runaway Gaps]]
