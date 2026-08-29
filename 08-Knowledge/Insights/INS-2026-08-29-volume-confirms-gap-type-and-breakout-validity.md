---
type: insight
date: 2026-08-29
actionability: 4
connection_type: adds_condition
domains: [concepts, patterns, rules]
sources: ["N150-price-gaps-types", "R082-breakouts-must-be-accompanied-by-heavy-volume", "C328-gaps"]
seed_id: gap_continuation_volume
tags: [insight, discovery, knowledge-evolution]
---

# Volume confirms gap type and breakout validity

## Discovery Summary

Rule R082 states that all price pattern breakouts require heavy volume for validation. The gap notes (N150, C328) classify breakaway gaps as signaling new trend starts but do not explicitly mention volume. Applying R082's volume condition to breakaway gaps creates a filter: a gap that appears to be breakaway but lacks heavy volume is likely a common gap or false signal, not a valid breakout. Similarly, exhaustion gaps at trend ends should show diminished volume relative to the preceding runaway gaps, adding a confirmatory dimension to gap identification.

## Trading Implication

Before treating any gap as a breakaway signal, confirm that volume is significantly above average; otherwise treat it as a common gap likely to fill. For exhaustion gaps, look for a volume spike followed by immediate reversal volume to distinguish from a continuation runaway gap.

## Supporting Notes

- [[N150-price-gaps-types]]
- [[R082-breakouts-must-be-accompanied-by-heavy-volume]]
- [[C328-gaps]]

## Connection Type

**adds_condition** — Actionability score: 4/5
