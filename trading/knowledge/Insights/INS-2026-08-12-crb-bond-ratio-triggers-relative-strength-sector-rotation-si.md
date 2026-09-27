---
type: insight
date: 2026-08-12
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
# CRB/Bond Ratio Triggers Relative Strength Sector Rotation Signals

## Discovery Summary

R249-sector-rotation-based-on-crbbond-ratio provides a specific intermarket trigger (CRB/Bond ratio direction) that can be combined with the relative strength methodology described in N112 and C340 to create a two-stage sector rotation process. Rather than rotating blindly based on the macro ratio alone, traders can use relative strength analysis (N112, C340) to confirm which specific inflation-sensitive or defensive stocks are actually outperforming before committing capital. The CRB/Bond ratio provides the macro directional bias, while relative strength provides the within-sector ranking to select the strongest individual securities.

## Trading Implication

When the CRB/Bond ratio turns upward, screen inflation-sensitive sectors (golds, oils, cyclicals) using relative strength analysis to rank candidates and buy only those showing confirmed outperformance versus benchmarks; reverse the screening into defensives when the ratio falls.

## Supporting Notes

- [[N112-relative-strength-analysis-for-sector-rotation]]
- [[R249-sector-rotation-based-on-crbbond-ratio]]
- [[C340-relative-strength-analysis-for-stocks-and-sectors]]

## Connection Type

**creates_filter** — Actionability score: 4/5

## Related Notes
- [[INS-2026-08-01-crb-bond-ratio-triggers-relative-strength-sector-rotation-si|CRB/Bond Ratio Triggers Relative Strength Sector Rotation Signal]]
