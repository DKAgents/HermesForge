---
type: insight
date: 2026-08-08
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
# CRB/Bond Ratio as Objective Filter for Relative Strength Sector Rotation

## Discovery Summary

R249-sector-rotation-based-on-crbbond-ratio provides a concrete, objective intermarket signal (rising vs. falling CRB/Bond ratio) that can serve as the macro regime filter for the relative strength analysis described in N112 and C340. Rather than applying relative strength analysis in a vacuum, the CRB/Bond ratio first determines which sector basket to screen — inflation-sensitive (golds, oils, cyclicals) when ratio rises, or defensive sectors (utilities, financials, consumer staples) when ratio falls — and then relative strength analysis within that basket identifies the strongest individual names to own. This two-step approach constrains the universe before applying the selection tool, improving signal quality.

## Trading Implication

A trader should first check the CRB/Bond ratio trend to determine the prevailing macro regime, then run relative strength analysis only within the regime-appropriate sector basket — buying the strongest stocks within cyclicals during rising ratio environments and within defensives during falling ratio environments.

## Supporting Notes

- [[N112-relative-strength-analysis-for-sector-rotation]]
- [[R249-sector-rotation-based-on-crbbond-ratio]]
- [[C340-relative-strength-analysis-for-stocks-and-sectors]]

## Connection Type

**creates_filter** — Actionability score: 4/5
