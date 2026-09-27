---
type: insight
date: 2026-08-04
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
# CRB/Bond Ratio Triggers Relative Strength Sector Rotation Decisions

## Discovery Summary

R249 provides a concrete intermarket signal (CRB/Bond ratio direction) that operationalizes the relative strength framework described in N112 and C340. Rather than using relative strength analysis in isolation to scan for outperformers, the CRB/Bond ratio acts as a macro filter that pre-determines which sector universe to apply relative strength analysis to — inflation-sensitive sectors (golds, oils, cyclicals) when rising, defensive sectors (utilities, financials, consumer staples) when falling. This creates a two-stage decision process: first confirm macro regime via CRB/Bond, then rank within the appropriate sector universe using relative strength.

## Trading Implication

A trader should first check CRB/Bond ratio trend direction to determine the correct sector universe, then apply relative strength analysis within that universe to select the strongest individual names — avoiding applying relative strength analysis across all sectors indiscriminately.

## Supporting Notes

- [[N112-relative-strength-analysis-for-sector-rotation]]
- [[R249-sector-rotation-based-on-crbbond-ratio]]
- [[C340-relative-strength-analysis-for-stocks-and-sectors]]

## Connection Type

**creates_filter** — Actionability score: 4/5

## Related Notes
- [[INS-2026-08-03-crb-bond-ratio-as-trigger-for-relative-strength-sector-rotat|CRB/Bond Ratio as Trigger for Relative Strength Sector Rotation]]
