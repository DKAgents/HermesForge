---
type: insight
date: 2026-08-12
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

N150 and C328 identify gap types with directional implications (breakaway=chase, exhaustion=fade), but neither provides a validation mechanism. R082 supplies the missing filter: volume must surge at breakaway gaps to confirm trend initiation, just as it must at pattern breakouts. Critically, exhaustion gaps — which signal trend endings and should be faded — often occur on high volume that then collapses, distinguishing them from breakaway gaps where sustained heavy volume follows.

## Trading Implication

Chase a gap only when it is accompanied by heavy volume AND subsequent volume sustains (consistent with breakaway behavior per R082); fade a gap when volume spikes then immediately collapses, signaling exhaustion — do not enter in the gap direction without this volume confirmation.

## Supporting Notes

- [[N150-price-gaps-types]]
- [[R082-breakouts-must-be-accompanied-by-heavy-volume]]
- [[C328-gaps]]

## Connection Type

**creates_filter** — Actionability score: 4/5
