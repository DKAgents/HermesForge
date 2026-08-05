---
type: insight
date: 2026-08-05
actionability: 4
connection_type: creates_filter
domains: [concepts, indicators, rules]
sources: ["N112-relative-strength-analysis-for-sector-rotation", "R249-sector-rotation-based-on-crbbond-ratio", "C340-relative-strength-analysis-for-stocks-and-sectors"]
seed_id: intermarket_sector_rotation
tags: [insight, discovery, knowledge-evolution]
---

# CRB/Bond Ratio as Trigger for Relative Strength Sector Rotation

## Discovery Summary

R249-sector-rotation-based-on-crbbond-ratio provides a specific intermarket signal (rising vs. falling CRB/Bond ratio) that can serve as the macro trigger for the relative strength screening process described in N112 and C340. Rather than running relative strength analysis on all sectors simultaneously, the CRB/Bond ratio first filters which sector universe to screen: inflation-sensitive (golds, oils, cyclicals) when rising, or defensives (utilities, financials, consumer staples) when falling. This creates a two-stage process where intermarket analysis narrows the candidate pool before relative strength rankings determine the best individual names within that pool.

## Trading Implication

A trader should first check the CRB/Bond ratio direction to determine which sector category is favored, then apply relative strength analysis only within that favored category to select the top-performing individual stocks or sub-sectors for allocation.

## Supporting Notes

- [[N112-relative-strength-analysis-for-sector-rotation]]
- [[R249-sector-rotation-based-on-crbbond-ratio]]
- [[C340-relative-strength-analysis-for-stocks-and-sectors]]

## Connection Type

**creates_filter** — Actionability score: 4/5
