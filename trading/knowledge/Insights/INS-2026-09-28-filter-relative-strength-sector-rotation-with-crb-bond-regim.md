---
type: insight
date: 2026-09-28
actionability: 4
connection_type: adds_condition
domains: [indicators, intermarket analysis, relative strength, sector rotation, trading rules]
sources: ["N112-relative-strength-analysis-for-sector-rotation", "R249-sector-rotation-based-on-crbbond-ratio"]
seed_id: intermarket_sector_rotation
tags: [insight, discovery, knowledge-evolution]
---

# Filter Relative-Strength Sector Rotation with CRB/Bond Regime

## Discovery Summary

N112 relative-strength-analysis-for-sector-rotation identifies strong sectors by relative strength, while R249 sector-rotation-based-on-crbbond-ratio uses the CRB/Bond ratio to set the intermarket rotation regime. Combining them adds a condition: only take long sector rotation signals from relative strength when the CRB/Bond ratio confirms the favored cyclical or defensive buckets. This turns two separate signals into a top-down regime filter followed by bottom-up relative-strength selection.

## Trading Implication

Use the CRB/Bond ratio as a regime gate; when it is rising, buy relative-strength leaders in commodity/cyclical sectors, and when it is falling, rotate into defensives or cash. Avoid fighting the CRB/Bond trend when selecting sectors by relative strength.

## Supporting Notes

- [[N112-relative-strength-analysis-for-sector-rotation]]
- [[R249-sector-rotation-based-on-crbbond-ratio]]

## Connection Type

**adds_condition** — Actionability score: 4/5
