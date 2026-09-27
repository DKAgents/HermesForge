---
type: insight
date: 2026-08-10
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
# CRB/Bond Ratio Gates Relative Strength Sector Rotation Decisions

## Discovery Summary

R249 provides a macro intermarket filter (CRB/Bond ratio direction) that determines WHICH sectors to scan, while N112 and C340 describe the relative strength methodology for ranking within those sectors. The non-obvious connection is that R249's ratio acts as a regime gate: only run relative strength analysis on inflation-sensitive stocks (golds, oils, cyclicals) when CRB/Bond is rising; switch the relative strength scan to defensives (utilities, financials, staples) when it is falling. This sequences macro intermarket signals before bottom-up relative strength ranking, preventing traders from selecting the strongest stock in the wrong sector regime.

## Trading Implication

A trader should first check the CRB/Bond ratio trend to identify the correct sector universe, then apply relative strength analysis within that universe to select the top-ranked individual names — never apply relative strength across all sectors simultaneously without this macro filter.

## Supporting Notes

- [[N112-relative-strength-analysis-for-sector-rotation]]
- [[R249-sector-rotation-based-on-crbbond-ratio]]
- [[C340-relative-strength-analysis-for-stocks-and-sectors]]

## Connection Type

**creates_filter** — Actionability score: 4/5
