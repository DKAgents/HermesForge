---
type: insight
date: 2026-08-15
actionability: 4
connection_type: adds_condition
domains: [concepts, patterns, rules]
sources: ["N150-price-gaps-types", "R082-breakouts-must-be-accompanied-by-heavy-volume", "C328-gaps"]
seed_id: gap_continuation_volume
tags: [insight, discovery, knowledge-evolution]
---

# Volume Validates Gap Type: Chase vs Fade Decision Rule

## Discovery Summary

N150 and C328 identify gap types with opposing implications: breakaway gaps signal trend initiation (chase), runaway gaps project continuation (chase), exhaustion gaps signal reversal (fade). R082 adds the critical filter missing from gap analysis alone — volume confirmation. A breakaway gap accompanied by heavy volume per R082 validates the chase signal; an exhaustion gap with diminishing volume reinforces the fade signal. Without volume context, gap type classification alone is insufficient for execution.

## Trading Implication

Chase a gap only when it is accompanied by a volume surge confirming it as breakaway or runaway; fade a gap (especially after a prolonged trend) when volume is thin or declining, signaling exhaustion and a likely reversal entry.

## Supporting Notes

- [[N150-price-gaps-types]]
- [[R082-breakouts-must-be-accompanied-by-heavy-volume]]
- [[C328-gaps]]

## Connection Type

**adds_condition** — Actionability score: 4/5
