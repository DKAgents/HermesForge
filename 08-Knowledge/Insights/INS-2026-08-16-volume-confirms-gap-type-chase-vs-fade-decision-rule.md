---
type: insight
date: 2026-08-16
actionability: 4
connection_type: adds_condition
domains: [concepts, patterns, rules]
sources: ["N150-price-gaps-types", "R082-breakouts-must-be-accompanied-by-heavy-volume", "C328-gaps"]
seed_id: gap_continuation_volume
tags: [insight, discovery, knowledge-evolution]
---

# Volume Confirms Gap Type: Chase vs Fade Decision Rule

## Discovery Summary

N150 and C328 establish that gap types carry different directional implications (breakaway = trend start to chase, exhaustion = trend end to fade), but neither note specifies how to distinguish them in real time. R082 provides the missing filter: breakaway gaps should be accompanied by heavy volume (confirming trend initiation), while exhaustion gaps typically occur on relatively lower or climactic volume. This creates a concrete decision rule: volume at the gap is the discriminating variable between chasing and fading.

## Trading Implication

When a gap forms, check volume immediately: a gap accompanied by surging volume signals a breakaway to be traded with the direction; a gap on diminishing or climactic-but-fading volume signals an exhaustion gap to be faded or used as a stop-entry against the prior trend.

## Supporting Notes

- [[N150-price-gaps-types]]
- [[R082-breakouts-must-be-accompanied-by-heavy-volume]]
- [[C328-gaps]]

## Connection Type

**adds_condition** — Actionability score: 4/5
