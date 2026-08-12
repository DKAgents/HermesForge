---
type: insight
date: 2026-08-06
actionability: 4
connection_type: creates_filter
domains: [concepts, indicators, rules]
sources: ["N112-relative-strength-analysis-for-sector-rotation", "R249-sector-rotation-based-on-crbbond-ratio", "C340-relative-strength-analysis-for-stocks-and-sectors"]
seed_id: intermarket_sector_rotation
tags: [insight, discovery, knowledge-evolution]
topic: knowledge
confidence: high
has_quotes: false
source: unknown
---
# CRB/Bond Ratio as Objective Filter for Relative Strength Sector Rotation

## Discovery Summary

R249 provides a specific, rules-based intermarket trigger (rising vs. falling CRB/Bond ratio) that defines WHICH sector rotation to execute, while N112 and C340 provide the relative strength methodology to identify the BEST individual stocks or sub-sectors within those inflation-sensitive or defensive categories. Together, the CRB/Bond ratio determines the macro regime, and relative strength analysis ranks candidates within the regime-appropriate sectors, creating a two-stage selection process. This combination prevents traders from using relative strength in isolation without a macro context, and prevents macro signals from being applied without stock-level precision.

## Trading Implication

A trader should first check the CRB/Bond ratio direction to determine the correct sector bucket (inflation-sensitive vs. defensive), then apply relative strength analysis within that bucket to rank and select the strongest individual stocks or sub-sectors for capital allocation.

## Supporting Notes

- [[N112-relative-strength-analysis-for-sector-rotation]]
- [[R249-sector-rotation-based-on-crbbond-ratio]]
- [[C340-relative-strength-analysis-for-stocks-and-sectors]]

## Connection Type

**creates_filter** — Actionability score: 4/5
