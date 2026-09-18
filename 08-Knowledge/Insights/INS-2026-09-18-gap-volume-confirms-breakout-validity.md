---
type: insight
date: 2026-09-18
actionability: 4
connection_type: adds_condition
domains: [concepts, patterns, rules]
sources: ["N150-price-gaps-types", "R082-breakouts-must-be-accompanied-by-heavy-volume", "C328-gaps"]
seed_id: gap_continuation_volume
tags: [insight, discovery, knowledge-evolution]
---

# Gap Volume Confirms Breakout Validity

## Discovery Summary

Note C328 defines gaps as spaces with no trading, while rule R082 states breakouts must be accompanied by heavy volume. Combining these, a gap at a breakout point (especially breakaway gaps) must show heavy volume to be a valid signal; a gap without volume suggests a common gap or false breakout. This directly ties the gap-type framework to the volume confirmation rule.

## Trading Implication

Do not trade a breakaway gap as a breakout signal unless volume is clearly above average; avoid chasing gaps that form on low volume as they are likely common gaps or false moves.

## Supporting Notes

- [[N150-price-gaps-types]]
- [[R082-breakouts-must-be-accompanied-by-heavy-volume]]
- [[C328-gaps]]

## Connection Type

**adds_condition** — Actionability score: 4/5
