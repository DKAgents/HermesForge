---
type: insight
date: 2026-09-14
actionability: 4
connection_type: adds_condition
domains: [concepts, patterns, rules]
sources: ["N150-price-gaps-types", "R082-breakouts-must-be-accompanied-by-heavy-volume", "C328-gaps"]
seed_id: gap_continuation_volume
tags: [insight, discovery, knowledge-evolution]
---

# Gap Breakouts Require Volume for Validity

## Discovery Summary

The notes on gap types (N150-price-gaps-types, C328-gaps) identify breakaway gaps as signals of new trends and runaway gaps as continuation signals, but they do not explicitly state a volume confirmation requirement. The rule R082-breakouts-must-be-accompanied-by-heavy-volume provides that condition: any price pattern breakout, including gap breakouts, must occur on heavier volume to be considered valid. Thus, a breakaway gap without volume surge may be a false signal, while a breakaway gap with volume increase is more reliable.

## Trading Implication

Traders should only enter on gap breakouts (up or down) if the gap day shows significantly higher volume than the preceding days; otherwise, treat the gap as suspect and avoid chasing.

## Supporting Notes

- [[N150-price-gaps-types]]
- [[R082-breakouts-must-be-accompanied-by-heavy-volume]]
- [[C328-gaps]]

## Connection Type

**adds_condition** — Actionability score: 4/5
