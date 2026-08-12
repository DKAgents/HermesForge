---
type: insight
date: 2026-08-11
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
# Volume Distinguishes Breakaway Gaps from Exhaustion Gaps to Chase

## Discovery Summary

N150 and C328 establish that different gap types have opposite implications: breakaway gaps signal trend starts (chase), while exhaustion gaps signal trend ends (fade). However, neither gap note alone provides a reliable filter to distinguish them in real time. R082 provides the missing discriminator: breakaway gaps should be accompanied by heavy volume, consistent with its rule that valid breakouts require surging volume. Exhaustion gaps, by contrast, typically occur on diminishing volume as a trend loses momentum.

## Trading Implication

When a gap occurs, check volume immediately: a gap with heavy/surging volume is a breakaway gap to chase; a gap with light or declining volume — especially after an extended trend — should be treated as a potential exhaustion gap to fade or avoid.

## Supporting Notes

- [[N150-price-gaps-types]]
- [[R082-breakouts-must-be-accompanied-by-heavy-volume]]
- [[C328-gaps]]

## Connection Type

**creates_filter** — Actionability score: 4/5
