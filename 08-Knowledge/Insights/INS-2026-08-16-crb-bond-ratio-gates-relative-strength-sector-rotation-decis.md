---
type: insight
date: 2026-08-16
actionability: 4
connection_type: creates_filter
domains: [concepts, indicators, rules]
sources: ["N112-relative-strength-analysis-for-sector-rotation", "R249-sector-rotation-based-on-crbbond-ratio", "C340-relative-strength-analysis-for-stocks-and-sectors"]
seed_id: intermarket_sector_rotation
tags: [insight, discovery, knowledge-evolution]
---

# CRB/Bond Ratio Gates Relative Strength Sector Rotation Decisions

## Discovery Summary

R249 provides a macro intermarket signal (CRB/Bond ratio direction) that determines WHICH sectors to apply relative strength analysis toward, while N112 and C340 provide the tool (relative strength) for ranking candidates within those sectors. The combination creates a two-stage filter: first, use CRB/Bond ratio to determine the inflationary regime and eligible sector universe (e.g., rising ratio → cyclicals/oils/golds; falling ratio → utilities/financials/staples), then apply relative strength analysis within that universe to select the strongest individual stocks or subsectors.

## Trading Implication

A trader should first check CRB/Bond ratio trend to identify the correct sector universe, then rank candidates within that universe using relative strength to concentrate capital in the highest-momentum names — avoiding relative strength analysis on sectors that conflict with the prevailing macro regime.

## Supporting Notes

- [[N112-relative-strength-analysis-for-sector-rotation]]
- [[R249-sector-rotation-based-on-crbbond-ratio]]
- [[C340-relative-strength-analysis-for-stocks-and-sectors]]

## Connection Type

**creates_filter** — Actionability score: 4/5
