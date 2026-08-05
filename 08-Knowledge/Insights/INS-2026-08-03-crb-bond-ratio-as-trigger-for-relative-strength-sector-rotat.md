---
type: insight
date: 2026-08-03
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
# CRB/Bond Ratio as Trigger for Relative Strength Sector Rotation

## Discovery Summary

R249 provides a concrete intermarket signal (CRB/Bond ratio direction) that can serve as the macro trigger for when to apply the relative strength screening described in N112 and C340. Rather than continuously running relative strength scans across all sectors, traders can use the CRB/Bond ratio as a regime filter: when rising, apply relative strength analysis specifically within inflation-sensitive sectors (golds, oils, cyclicals); when falling, redirect relative strength scanning toward defensive sectors (utilities, financials, consumer staples). This sequences the two tools — intermarket signal first, then relative strength ranking within the signaled sector group — creating a two-stage selection process.

## Trading Implication

Monitor the CRB/Bond ratio weekly to determine which sector basket to scan; then use relative strength analysis to rank and select the strongest individual stocks only within that macro-confirmed basket, avoiding cross-basket comparisons that could lead to buying a strong defensive stock during an inflationary regime or vice versa.

## Supporting Notes

- [[N112-relative-strength-analysis-for-sector-rotation]]
- [[R249-sector-rotation-based-on-crbbond-ratio]]
- [[C340-relative-strength-analysis-for-stocks-and-sectors]]

## Connection Type

**creates_filter** — Actionability score: 4/5
