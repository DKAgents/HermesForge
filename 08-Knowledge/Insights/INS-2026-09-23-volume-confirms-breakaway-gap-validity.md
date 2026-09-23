---
type: insight
date: 2026-09-23
actionability: 4
connection_type: adds_condition
domains: [concepts, patterns, rules]
sources: ["N150-price-gaps-types", "R082-breakouts-must-be-accompanied-by-heavy-volume", "C328-gaps"]
seed_id: gap_continuation_volume
tags: [insight, discovery, knowledge-evolution]
---

# Volume confirms breakaway gap validity

## Discovery Summary

The pattern note (N150-price-gaps-types) defines breakaway gaps as signaling the start of a new trend, while the rule note (R082-breakouts-must-be-accompanied-by-heavy-volume) states that all breakout signals require heavy volume to be valid. Since a breakaway gap is a form of breakout, this rule adds a critical confirmation condition: a breakaway gap without elevated volume is suspect and likely false.

## Trading Implication

Only enter trades on breakaway gaps when the gap day's volume is significantly above the recent average; ignore or fade gaps that occur on low or average volume.

## Supporting Notes

- [[N150-price-gaps-types]]
- [[R082-breakouts-must-be-accompanied-by-heavy-volume]]
- [[C328-gaps]]

## Connection Type

**adds_condition** — Actionability score: 4/5
