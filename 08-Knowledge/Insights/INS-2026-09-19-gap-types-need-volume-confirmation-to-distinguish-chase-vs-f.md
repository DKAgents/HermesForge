---
type: insight
date: 2026-09-19
actionability: 4
connection_type: adds_condition
domains: [concepts, patterns, rules]
sources: ["N150-price-gaps-types", "R082-breakouts-must-be-accompanied-by-heavy-volume", "C328-gaps"]
seed_id: gap_continuation_volume
tags: [insight, discovery, knowledge-evolution]
---

# Gap types need volume confirmation to distinguish chase vs fade

## Discovery Summary

N150-price-gaps-types classifies breakaway gaps as new-trend signals and exhaustion gaps as end-of-trend signals, while C328-gaps notes up/down gaps reflect strength/weakness. R082-breakouts-must-be-accompanied-by-heavy-volume adds the missing filter: a gap acting as a breakout from a price pattern is only valid if accompanied by heavier volume. Therefore, volume is the key condition separating a tradeable breakaway gap from a false/common gap or an exhaustion gap that should not be chased.

## Trading Implication

Chase a breakaway gap only when volume expands at the gap; fade trends only after an exhaustion gap is followed by an opposite breakaway gap confirmed by heavy volume.

## Supporting Notes

- [[N150-price-gaps-types]]
- [[R082-breakouts-must-be-accompanied-by-heavy-volume]]
- [[C328-gaps]]

## Connection Type

**adds_condition** — Actionability score: 4/5
