---
type: insight
date: 2026-09-09
actionability: 4
connection_type: creates_filter
domains: [concepts, indicators, rules]
sources: ["N112-relative-strength-analysis-for-sector-rotation", "R249-sector-rotation-based-on-crbbond-ratio", "C340-relative-strength-analysis-for-stocks-and-sectors"]
seed_id: intermarket_sector_rotation
tags: [insight, discovery, knowledge-evolution]
---

# RS-filtered sector rotation using CRB/Bond signal

## Discovery Summary

R249 provides a macro rotation rule based on the CRB/Bond ratio: when rising, buy inflation-sensitive sectors (gold, oil, cyclicals); when falling, rotate to defensives. N112 and C340 describe using relative strength analysis to find outperforming assets within a universe. Combining these, the CRB/Bond signal defines the favored sector basket, and relative strength acts as a secondary filter to select only the strongest individual stocks or industry groups within that macro-favored sector.

## Trading Implication

When the CRB/Bond ratio turns decisively higher, instead of indiscriminately buying all inflation-sensitive stocks, use relative strength analysis to isolate and trade only those that are outperforming their sector peers.

## Supporting Notes

- [[N112-relative-strength-analysis-for-sector-rotation]]
- [[R249-sector-rotation-based-on-crbbond-ratio]]
- [[C340-relative-strength-analysis-for-stocks-and-sectors]]

## Connection Type

**creates_filter** — Actionability score: 4/5
