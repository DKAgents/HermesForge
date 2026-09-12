---
type: insight
date: 2026-09-12
actionability: 4
connection_type: creates_filter
domains: [concepts, indicators, rules]
sources: ["N112-relative-strength-analysis-for-sector-rotation", "R249-sector-rotation-based-on-crbbond-ratio", "C340-relative-strength-analysis-for-stocks-and-sectors"]
seed_id: intermarket_sector_rotation
tags: [insight, discovery, knowledge-evolution]
---

# Relative Strength Filter Refines CRB/Bond Sector Rotation

## Discovery Summary

R249 establishes a macro rotation rule: when the CRB/Bond ratio rises, favor inflation-sensitive sectors like golds, oils, and cyclicals; when it falls, favor defensive sectors like utilities, financials, and staples. N112 and C340 describe using relative strength analysis to identify the strongest-performing sectors and stocks. Combining them means using the CRB/Bond ratio to define the eligible sector universe, then applying relative strength ranking to select only the highest-momentum names within that universe.

## Trading Implication

When the CRB/Bond ratio trends up, a trader should first isolate inflation-sensitive sectors, then buy only those with the strongest relative strength versus the broad market; when the ratio trends down, apply the same filter to defensive sectors.

## Supporting Notes

- [[N112-relative-strength-analysis-for-sector-rotation]]
- [[R249-sector-rotation-based-on-crbbond-ratio]]
- [[C340-relative-strength-analysis-for-stocks-and-sectors]]

## Connection Type

**creates_filter** — Actionability score: 4/5
