---
type: insight
date: 2026-08-30
actionability: 4
connection_type: creates_filter
domains: [concepts, indicators, rules]
sources: ["N112-relative-strength-analysis-for-sector-rotation", "R249-sector-rotation-based-on-crbbond-ratio", "C340-relative-strength-analysis-for-stocks-and-sectors"]
seed_id: intermarket_sector_rotation
tags: [insight, discovery, knowledge-evolution]
---

# Filter sector rotation candidates using intermarket regime before ranking

## Discovery Summary

R249 defines a macro regime filter using the CRB/Bond ratio to determine whether to favor inflation-sensitive sectors (golds, oils, cyclicals) or defensive sectors (utilities, financials, consumer staples). N112 and C340 describe using relative strength analysis to rank sectors and stocks for outperformance. By using the CRB/Bond ratio to first establish the permitted sector universe based on the inflation/deflation regime, a trader can then apply relative strength rankings only within that pre-filtered set, avoiding false strength signals in sectors misaligned with the macro environment.

## Trading Implication

Before running relative strength rankings, check the CRB/Bond ratio direction; if rising, restrict the relative strength analysis universe to inflation-sensitive sectors only; if falling, restrict it to defensive sectors only. Then allocate capital to the top-ranked sectors and stocks within that filtered universe.

## Supporting Notes

- [[N112-relative-strength-analysis-for-sector-rotation]]
- [[R249-sector-rotation-based-on-crbbond-ratio]]
- [[C340-relative-strength-analysis-for-stocks-and-sectors]]

## Connection Type

**creates_filter** — Actionability score: 4/5
