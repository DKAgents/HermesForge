---
type: insight
date: 2026-08-13
actionability: 4
connection_type: creates_filter
domains: [concepts, indicators, rules]
sources: ["N112-relative-strength-analysis-for-sector-rotation", "R249-sector-rotation-based-on-crbbond-ratio", "C340-relative-strength-analysis-for-stocks-and-sectors"]
seed_id: intermarket_sector_rotation
tags: [insight, discovery, knowledge-evolution]
---

# CRB/Bond Ratio as Objective Filter for Relative Strength Sector Rotation

## Discovery Summary

R249 provides a concrete intermarket signal (CRB/Bond ratio direction) that can serve as an objective entry condition for the relative strength rotation process described in N112 and C340. Rather than using relative strength analysis in isolation, a trader can first use the CRB/Bond ratio to determine the macro regime (inflationary vs deflationary), then apply relative strength analysis within that regime's favored sectors to select the strongest individual names. This sequences the two tools: intermarket ratio sets the sector universe, relative strength ranks within it.

## Trading Implication

When CRB/Bond ratio is rising, screen only inflation-sensitive sectors (golds, oils, cyclicals) using relative strength to pick the top performers; when falling, restrict the relative strength screen to defensives (utilities, financials, consumer staples) — avoiding cross-regime allocation errors.

## Supporting Notes

- [[N112-relative-strength-analysis-for-sector-rotation]]
- [[R249-sector-rotation-based-on-crbbond-ratio]]
- [[C340-relative-strength-analysis-for-stocks-and-sectors]]

## Connection Type

**creates_filter** — Actionability score: 4/5
