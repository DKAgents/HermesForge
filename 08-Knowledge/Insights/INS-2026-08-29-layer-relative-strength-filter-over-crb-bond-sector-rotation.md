---
type: insight
date: 2026-08-29
actionability: 4
connection_type: creates_filter
domains: [concepts, indicators, rules]
sources: ["N112-relative-strength-analysis-for-sector-rotation", "R249-sector-rotation-based-on-crbbond-ratio", "C340-relative-strength-analysis-for-stocks-and-sectors"]
seed_id: intermarket_sector_rotation
tags: [insight, discovery, knowledge-evolution]
---

# Layer relative strength filter over CRB/Bond sector rotation

## Discovery Summary

R249 dictates sector exposure based on the CRB/Bond ratio: rising favors inflation-sensitive stocks (gold, oil, cyclicals), falling favors defensives. N112 and C340 describe relative strength analysis to isolate individual stocks or sub-sectors outperforming the broader market. Combining these — using the macro intermarket ratio to set the sector universe, then applying relative strength within that universe — creates a two-stage filter that refines entry timing and selection.

## Trading Implication

When the CRB/Bond ratio rises, a trader should first restrict their watchlist to inflation-sensitive sectors, then only take positions in stocks or industry groups within those sectors showing the highest relative strength versus a benchmark like the S&P 500.

## Supporting Notes

- [[N112-relative-strength-analysis-for-sector-rotation]]
- [[R249-sector-rotation-based-on-crbbond-ratio]]
- [[C340-relative-strength-analysis-for-stocks-and-sectors]]

## Connection Type

**creates_filter** — Actionability score: 4/5
