---
type: insight
date: 2026-09-25
actionability: 4
connection_type: reveals_sequence
domains: [filter rule, intermarket analysis, relative strength, sector rotation]
sources: ["N112-relative-strength-analysis-for-sector-rotation", "R249-sector-rotation-based-on-crbbond-ratio", "C340-relative-strength-analysis-for-stocks-and-sectors"]
seed_id: intermarket_sector_rotation
tags: [insight, discovery, knowledge-evolution]
---

# CRB/Bond Regime Filters Relative Strength for Sector Rotation

## Discovery Summary

R249 uses the CRB/Bond ratio to set a sector bias: buy golds, oils, and cyclicals when it is rising, and rotate into utilities, financials, and consumer staples when it is falling. N112 and C340 add that relative strength analysis identifies which of those sectors are actually outperforming the broader market. Taken sequentially, the CRB/Bond ratio acts as a regime filter, and relative strength acts as a selector within the favored group, preventing capital from being placed in weak members of the correct basket.

## Trading Implication

First confirm whether the CRB/Bond ratio is rising or falling, then buy only the strongest relative-strength sectors from the corresponding list—cyclicals when the ratio is rising, defensives when it is falling.

## Supporting Notes

- [[N112-relative-strength-analysis-for-sector-rotation]]
- [[R249-sector-rotation-based-on-crbbond-ratio]]
- [[C340-relative-strength-analysis-for-stocks-and-sectors]]

## Connection Type

**reveals_sequence** — Actionability score: 4/5
