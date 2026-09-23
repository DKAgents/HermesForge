---
type: insight
date: 2026-09-23
actionability: 4
connection_type: creates_filter
domains: [concepts, indicators, rules]
sources: ["N112-relative-strength-analysis-for-sector-rotation", "R249-sector-rotation-based-on-crbbond-ratio", "C340-relative-strength-analysis-for-stocks-and-sectors"]
seed_id: intermarket_sector_rotation
tags: [insight, discovery, knowledge-evolution]
---

# Filter sectors via CRB/Bond then rank with RS

## Discovery Summary

Note R249 uses the CRB/Bond ratio to determine the macro regime (rising = inflation-sensitive sectors, falling = defensive sectors). Notes N112 and C340 advocate relative strength to identify the strongest sectors or stocks within the broader market. Combining them creates a two-step filter: first use the CRB/Bond ratio to restrict the universe to appropriate sectors, then apply relative strength to select the top performers within that subset.

## Trading Implication

When CRB/Bond is rising, screen for relative strength among gold, oil, and cyclical stocks; when falling, screen for relative strength among utilities, financials, and consumer staples. Only trade positions that pass both filters.

## Supporting Notes

- [[N112-relative-strength-analysis-for-sector-rotation]]
- [[R249-sector-rotation-based-on-crbbond-ratio]]
- [[C340-relative-strength-analysis-for-stocks-and-sectors]]

## Connection Type

**creates_filter** — Actionability score: 4/5
