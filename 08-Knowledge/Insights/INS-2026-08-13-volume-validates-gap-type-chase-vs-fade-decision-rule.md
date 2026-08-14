---
type: insight
date: 2026-08-13
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
# Volume Validates Gap Type: Chase vs Fade Decision Rule

## Discovery Summary

N150 and C328 establish that gap types have opposite trading implications — breakaway/runaway gaps signal trend continuation (chase), while exhaustion gaps signal reversal (fade). R082 provides the critical discriminating variable: volume. Since breakaway gaps should be accompanied by heavy volume (per R082's rule for valid breakouts), a gap with surging volume is more likely a breakaway (chase signal), while a gap occurring after a prolonged trend on declining or average volume is more likely an exhaustion gap (fade signal). This volume-gap interaction creates a mechanical filter absent from any single note.

## Trading Implication

When a price gap forms, require a volume surge relative to recent average to classify it as a breakaway/runaway gap worth chasing; gaps on weak or average volume after extended trends should be treated as potential exhaustion gaps and faded rather than followed.

## Supporting Notes

- [[N150-price-gaps-types]]
- [[R082-breakouts-must-be-accompanied-by-heavy-volume]]
- [[C328-gaps]]

## Connection Type

**creates_filter** — Actionability score: 4/5
