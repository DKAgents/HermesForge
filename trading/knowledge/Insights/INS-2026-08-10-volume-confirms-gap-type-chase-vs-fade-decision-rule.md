---
type: insight
date: 2026-08-10
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
# Volume Confirms Gap Type: Chase vs Fade Decision Rule

## Discovery Summary

N150-price-gaps-types and C328-gaps identify three actionable gap types (breakaway=chase, runaway=chase/measure, exhaustion=fade), but neither specifies how to distinguish them in real-time. R082-breakouts-must-be-accompanied-by-heavy-volume provides the missing filter: breakaway and runaway gaps (both signal continuation) should be accompanied by heavy volume per Murphy's rule, while exhaustion gaps — which signal trend endings — characteristically occur on diminishing or climactic volume that fails to sustain. This cross-domain combination creates a concrete decision rule: gap direction plus volume confirmation determines whether to chase or fade.

## Trading Implication

When a gap occurs, check volume immediately: a gap on surging volume relative to recent average suggests a breakaway or runaway gap — chase the direction; a gap on declining or climactic exhaustion-style volume after a prolonged trend suggests an exhaustion gap — fade it or avoid entry in the gap's direction.

## Supporting Notes

- [[N150-price-gaps-types]]
- [[R082-breakouts-must-be-accompanied-by-heavy-volume]]
- [[C328-gaps]]

## Connection Type

**adds_condition** — Actionability score: 4/5

## Related Notes
- [[N161-runaway-gaps|Runaway Gaps]]
