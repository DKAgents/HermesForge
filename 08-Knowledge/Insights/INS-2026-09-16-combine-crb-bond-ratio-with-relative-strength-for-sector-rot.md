---
type: insight
date: 2026-09-16
actionability: 4
connection_type: adds_condition
domains: [concepts, indicators, rules]
sources: ["N112-relative-strength-analysis-for-sector-rotation", "R249-sector-rotation-based-on-crbbond-ratio", "C340-relative-strength-analysis-for-stocks-and-sectors"]
seed_id: intermarket_sector_rotation
tags: [insight, discovery, knowledge-evolution]
---

# Combine CRB/Bond ratio with relative strength for sector rotation

## Discovery Summary

Rule R249 provides a macro timing signal: when the CRB/Bond ratio rises, buy inflation-sensitive sectors; when it falls, rotate to defensive sectors. Notes N112 and C340 advocate using relative strength analysis to identify the strongest sectors within those categories. By combining them, a trader can use the CRB/Bond ratio to determine the broad rotation direction, then apply relative strength to select the top-performing specific sectors or stocks within the targeted group, improving entry and allocation precision.

## Trading Implication

When the CRB/Bond ratio changes trend, run a relative strength ranking of sectors in the favored category (e.g., inflation-sensitive or defensive) and allocate capital to the top-ranked sectors or stocks, not just any sector in that group.

## Supporting Notes

- [[N112-relative-strength-analysis-for-sector-rotation]]
- [[R249-sector-rotation-based-on-crbbond-ratio]]
- [[C340-relative-strength-analysis-for-stocks-and-sectors]]

## Connection Type

**adds_condition** — Actionability score: 4/5
