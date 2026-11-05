---
type: insight
date: 2026-11-04
actionability: 4
connection_type: adds_condition
domains: [concepts, patterns, rules]
sources: ["N150-price-gaps-types", "R082-breakouts-must-be-accompanied-by-heavy-volume", "C328-gaps"]
seed_id: gap_continuation_volume
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# Volume Confirms Breakaway Gaps as Valid Breakouts

## Discovery Summary

N150-price-gaps-types defines breakaway gaps as signals of new trends, while R082-breakouts-must-be-accompanied-by-heavy-volume states that all breakouts require heavier volume to be valid. Combining these, a breakaway gap is only a reliable entry signal if it occurs on above-average volume; otherwise it may be a common gap or a false breakout. C328-gaps reinforces that up gaps indicate strength and down gaps weakness, but volume is the filter that distinguishes real breakaway gaps from noise.

## Trading Implication

When a gap appears, immediately check volume: if it is a breakaway gap with high volume, trade in the gap direction; if volume is low or declining, treat the gap as suspect and wait for confirmation or fade it.

## Supporting Notes

- [[N150-price-gaps-types]]
- [[R082-breakouts-must-be-accompanied-by-heavy-volume]]
- [[C328-gaps]]

## Connection Type

**adds_condition** — Actionability score: 4/5
