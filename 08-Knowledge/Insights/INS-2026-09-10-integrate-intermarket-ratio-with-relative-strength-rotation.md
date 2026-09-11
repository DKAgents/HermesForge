---
type: insight
date: 2026-09-10
actionability: 4
connection_type: adds_condition
domains: [concepts, indicators, rules]
sources: ["N112-relative-strength-analysis-for-sector-rotation", "R249-sector-rotation-based-on-crbbond-ratio", "C340-relative-strength-analysis-for-stocks-and-sectors"]
seed_id: intermarket_sector_rotation
tags: [insight, discovery, knowledge-evolution]
topic: knowledge
confidence: high
has_quotes: false
source: unknown
---
# Integrate Intermarket Ratio with Relative Strength Rotation

## Discovery Summary

R249-sector-rotation-based-on-crbbond-ratio provides a macro-level rule: rotate into inflation-sensitive sectors (golds, oils, cyclicals) when the CRB/Bond ratio rises, and into defensives (utilities, staples) when it falls. N112-relative-strength-analysis-for-sector-rotation and C340-relative-strength-analysis-for-stocks-and-sectors offer a selection mechanism within those macro groups. By applying relative strength analysis to rank stocks within the CRB/Bond-indicated sector basket, a trader filters for the strongest individual names within the already-favored macro category, adding a timing and selection layer to the broad rotation signal.

## Trading Implication

When the CRB/Bond ratio signals a sector rotation (per R249), use relative strength analysis (N112, C340) to select only the top-performing individual stocks within that favored sector rather than buying the entire sector or group blindly.

## Supporting Notes

- [[N112-relative-strength-analysis-for-sector-rotation]]
- [[R249-sector-rotation-based-on-crbbond-ratio]]
- [[C340-relative-strength-analysis-for-stocks-and-sectors]]

## Connection Type

**adds_condition** — Actionability score: 4/5
