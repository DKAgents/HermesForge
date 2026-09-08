---
type: insight
date: 2026-09-08
actionability: 4
connection_type: adds_condition
domains: [concepts, indicators, rules]
sources: ["N112-relative-strength-analysis-for-sector-rotation", "R249-sector-rotation-based-on-crbbond-ratio", "C340-relative-strength-analysis-for-stocks-and-sectors"]
seed_id: intermarket_sector_rotation
tags: [insight, discovery, knowledge-evolution]
---

# Layer CRB/Bond Filter Before Sector Relative Strength Ranking

## Discovery Summary

R249 specifies that CRB/Bond ratio direction dictates which sectors to favor (inflation-sensitive vs. defensive). Separately, N112 and C340 describe using relative strength analysis to identify outperforming sectors. A trader can combine these by first using the CRB/Bond ratio's trend to determine the eligible sector universe, then applying relative strength ranking within that filtered subset to select the specific strongest sectors for capital allocation.

## Trading Implication

When the CRB/Bond ratio is rising, rank only inflation-sensitive sectors (golds, oils, cyclicals) by relative strength and buy the leaders; when the ratio is falling, rank only defensive sectors (utilities, financials, staples) and rotate into the strongest of those.

## Supporting Notes

- [[N112-relative-strength-analysis-for-sector-rotation]]
- [[R249-sector-rotation-based-on-crbbond-ratio]]
- [[C340-relative-strength-analysis-for-stocks-and-sectors]]

## Connection Type

**adds_condition** — Actionability score: 4/5
