---
type: insight
date: 2026-09-03
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
# Intermarket CRB/Bond filter + relative strength selection

## Discovery Summary

R249 provides a macro-level rotation rule based on the CRB/Bond ratio: when rising, favor inflation-sensitive sectors (golds, oils, cyclicals); when falling, favor defensives (utilities, financials, consumer staples). N112 and C340 describe how relative strength analysis identifies outperforming sectors and stocks within a group. Combining them, a trader can first use the CRB/Bond ratio to define the eligible sector universe, then apply relative strength analysis to that universe to select only the strongest-performing sectors or stocks.

## Trading Implication

Instead of indiscriminately buying all sectors signaled by the CRB/Bond ratio, rank them by relative strength and allocate capital only to the top performers within the favored group.

## Supporting Notes

- [[N112-relative-strength-analysis-for-sector-rotation]]
- [[R249-sector-rotation-based-on-crbbond-ratio]]
- [[C340-relative-strength-analysis-for-stocks-and-sectors]]

## Connection Type

**creates_filter** — Actionability score: 4/5
