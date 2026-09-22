---
type: insight
date: 2026-09-22
actionability: 4
connection_type: adds_condition
domains: [concepts, indicators, rules]
sources: ["N112-relative-strength-analysis-for-sector-rotation", "R249-sector-rotation-based-on-crbbond-ratio", "C340-relative-strength-analysis-for-stocks-and-sectors"]
seed_id: intermarket_sector_rotation
tags: [insight, discovery, knowledge-evolution]
---

# CRB/Bond Ratio as Rotation Filter Enhances Relative Strength Signals

## Discovery Summary

R249-sector-rotation-based-on-crbbond-ratio defines a clear directional bias for sector exposure based on the CRB/Bond ratio (rising → own golds, oils, cyclicals; falling → own defensives). The relative strength notes (N112, C340) identify which specific stocks/sectors are currently outperforming. By combining them, a trader can apply the CRB/Bond ratio as a macro filter: when it is rising, only take long relative strength signals in inflation-sensitive sectors, and when it is falling, avoid those and rotate into defensive sectors that also show relative strength. This creates a condition where relative strength signals are only acted upon if they align with the intermarket regime, resolving potential conflicts between momentum and macro trends.

## Trading Implication

A trader should first determine the CRB/Bond ratio direction, then restrict long relative-strength entries to sectors that match the expected inflation/deflation regime (e.g., golds/oils/cyclicals when rising, utilities/financials/staples when falling). This filters out conflicting relative strength signals and increases the probability of sector rotation trades.

## Supporting Notes

- [[N112-relative-strength-analysis-for-sector-rotation]]
- [[R249-sector-rotation-based-on-crbbond-ratio]]
- [[C340-relative-strength-analysis-for-stocks-and-sectors]]

## Connection Type

**adds_condition** — Actionability score: 4/5
