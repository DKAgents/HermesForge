---
type: insight
date: 2026-08-28
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
# Macro CRB/Bond Filter Plus Relative Strength Sector Selection

## Discovery Summary

R249-sector-rotation-based-on-crbbond-ratio defines the macro regime: when the CRB/Bond ratio rises, favor inflation-sensitive sectors like golds, oils, and cyclicals; when it falls, favor defensives like utilities, financials, and consumer staples. N112-relative-strength-analysis-for-sector-rotation and C340-relative-strength-analysis-for-stocks-and-sectors provide a way to rank sectors and stocks against benchmarks. Combining them creates a two-stage filter: first use the CRB/Bond ratio to set the eligible sector universe, then use relative strength to select the strongest names within that universe.

## Trading Implication

When the CRB/Bond ratio is rising, rank inflation-sensitive sectors and stocks by relative strength and buy the leaders; when it is falling, rank defensive sectors and stocks by relative strength and rotate into the leaders.

## Supporting Notes

- [[N112-relative-strength-analysis-for-sector-rotation]]
- [[R249-sector-rotation-based-on-crbbond-ratio]]
- [[C340-relative-strength-analysis-for-stocks-and-sectors]]

## Connection Type

**creates_filter** — Actionability score: 4/5
