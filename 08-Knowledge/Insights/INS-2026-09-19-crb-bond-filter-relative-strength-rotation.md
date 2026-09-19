---
type: insight
date: 2026-09-19
actionability: 4
connection_type: reveals_sequence
domains: [concepts, indicators, rules]
sources: ["N112-relative-strength-analysis-for-sector-rotation", "R249-sector-rotation-based-on-crbbond-ratio", "C340-relative-strength-analysis-for-stocks-and-sectors"]
seed_id: intermarket_sector_rotation
tags: [insight, discovery, knowledge-evolution]
---

# CRB/Bond Filter + Relative Strength Rotation

## Discovery Summary

R249 provides a macro filter using the CRB/Bond ratio to determine whether to buy inflation-sensitive sectors (rising ratio) or defensive sectors (falling ratio). N112 and C340 then supply the relative strength methodology to identify the specific outperforming sectors within those categories, creating a two-step rotation process.

## Trading Implication

First check the CRB/Bond ratio trend to set the broad sector bias, then apply relative strength analysis to select the strongest individual sectors or stocks within the chosen group.

## Supporting Notes

- [[N112-relative-strength-analysis-for-sector-rotation]]
- [[R249-sector-rotation-based-on-crbbond-ratio]]
- [[C340-relative-strength-analysis-for-stocks-and-sectors]]

## Connection Type

**reveals_sequence** — Actionability score: 4/5
