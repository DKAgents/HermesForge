---
type: insight
date: 2026-09-18
actionability: 4
connection_type: adds_condition
domains: [concepts, indicators, rules]
sources: ["N112-relative-strength-analysis-for-sector-rotation", "R249-sector-rotation-based-on-crbbond-ratio", "C340-relative-strength-analysis-for-stocks-and-sectors"]
seed_id: intermarket_sector_rotation
tags: [insight, discovery, knowledge-evolution]
topic: knowledge
confidence: high
has_quotes: false
source: unknown
---
# CRB/Bond ratio plus relative strength for rotation

## Discovery Summary

The rule R249 provides a macro signal (CRB/Bond ratio) to determine whether to rotate into inflation-sensitive sectors (rising ratio) or defensive sectors (falling ratio). The relative strength analysis from N112 and C340 can then be applied to select the strongest individual stocks or sub-sectors within those chosen groups, adding a micro-level filter to the macro rotation decision.

## Trading Implication

A trader should first check the CRB/Bond ratio trend to decide the broad sector allocation, then use relative strength rankings to pick the top-performing stocks or ETFs within those sectors for entry.

## Supporting Notes

- [[N112-relative-strength-analysis-for-sector-rotation]]
- [[R249-sector-rotation-based-on-crbbond-ratio]]
- [[C340-relative-strength-analysis-for-stocks-and-sectors]]

## Connection Type

**adds_condition** — Actionability score: 4/5
