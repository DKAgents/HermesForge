---
type: insight
date: 2026-08-21
actionability: 4
connection_type: adds_condition
domains: [concepts, patterns, rules]
sources: ["N150-price-gaps-types", "R082-breakouts-must-be-accompanied-by-heavy-volume", "C328-gaps"]
seed_id: gap_continuation_volume
tags: [insight, discovery, knowledge-evolution]
topic: knowledge
confidence: high
has_quotes: false
source: unknown
---
# Volume Requirement Differentiates Breakaway Gaps from Fades

## Discovery Summary

N150 and C328 classify gaps into types with opposing implications — breakaway gaps signal new trends (chase), while exhaustion gaps signal trend endings (fade). R082 adds the critical missing filter: volume. A breakaway gap should be accompanied by heavy volume to confirm validity (R082), while an exhaustion gap typically occurs on declining or average volume. This volume condition, layered onto gap-type classification, creates a concrete decision rule absent from either gap note alone.

## Trading Implication

When a gap occurs, classify the type (breakaway vs exhaustion) using trend context, then confirm with volume: chase a breakaway gap only if accompanied by a surge in volume; fade or treat cautiously any gap on light volume at trend extremes as a probable exhaustion signal.

## Supporting Notes

- [[N150-price-gaps-types]]
- [[R082-breakouts-must-be-accompanied-by-heavy-volume]]
- [[C328-gaps]]

## Connection Type

**adds_condition** — Actionability score: 4/5
