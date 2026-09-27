---
type: insight
date: 2026-08-22
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
# Volume Confirms Which Gap Type to Chase vs Fade

## Discovery Summary

N150 and C328 establish that gap types carry different directional implications — breakaway gaps signal new trends (chase), runaway gaps project continuation (chase), and exhaustion gaps signal reversals (fade). R082 provides the missing confirmation filter: a breakaway gap should be accompanied by heavy volume to validate the chase signal, while an exhaustion gap appearing on diminishing volume strengthens the fade case. Without volume confirmation from R082, a trader cannot reliably distinguish a breakaway gap from a common or exhaustion gap at the moment of formation.

## Trading Implication

Chase an up gap only when accompanied by a volume surge (R082 threshold), treating it as a breakaway or runaway gap; fade or avoid a gap on low or declining volume as it more likely represents a common or exhaustion gap requiring confirmation before entry.

## Supporting Notes

- [[N150-price-gaps-types]]
- [[R082-breakouts-must-be-accompanied-by-heavy-volume]]
- [[C328-gaps]]

## Connection Type

**adds_condition** — Actionability score: 4/5

## Related Notes
- [[N161-runaway-gaps|Runaway Gaps]]
