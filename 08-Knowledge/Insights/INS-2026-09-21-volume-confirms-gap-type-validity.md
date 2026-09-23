---
type: insight
date: 2026-09-21
actionability: 4
connection_type: adds_condition
domains: [patterns, rules]
sources: ["N150-price-gaps-types", "R082-breakouts-must-be-accompanied-by-heavy-volume", "C328-gaps"]
seed_id: gap_continuation_volume
tags: [insight, discovery, knowledge-evolution]
topic: knowledge
confidence: high
has_quotes: false
source: unknown
---
# Volume Confirms Gap Type Validity

## Discovery Summary

The gap types note (N150) defines breakaway, runaway, and exhaustion gaps by their position in a trend, while rule R082 states that all breakout signals require heavy volume. Applying R082 to gaps means a breakaway gap must show a volume surge to be a valid trend start signal, and a gap without volume is likely a common gap to be ignored. This resolves ambiguity in gap trading by making volume a condition for acting on gap signals.

## Trading Implication

When trading gaps, only act on breakaway or runaway gaps that are accompanied by a clear volume surge; treat gaps with low or declining volume as common/false signals and avoid chasing or fading them.

## Supporting Notes

- [[N150-price-gaps-types]]
- [[R082-breakouts-must-be-accompanied-by-heavy-volume]]
- [[C328-gaps]]

## Connection Type

**adds_condition** — Actionability score: 4/5

## Related Notes
- [[INS-2026-09-20-volume-confirms-gap-type-for-valid-signals|Volume Confirms Gap Type for Valid Signals]]
- [[N161-runaway-gaps|Runaway Gaps]]
