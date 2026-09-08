---
type: insight
date: 2026-09-07
actionability: 5
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
# RS Refines Sector Rotation Based on CRB/Bond Ratio

## Discovery Summary

The CRB/Bond ratio from R249 provides a macro-level intermarket signal dictating whether to favor inflation-sensitive sectors (golds, oils, cyclicals) or defensive sectors (utilities, financials, consumer staples). Relative strength analysis, as described in N112 and C340, can then be applied to these prompted sector groups to select only those stocks or subsectors showing actual outperformance against benchmarks. This combination filters the rotation signal, replacing a blanket sector allocation with a targeted relative-strength-driven selection within the favored economic regime.

## Trading Implication

When the CRB/Bond ratio rises, do not blindly buy all golds, oils, and cyclicals; instead, use relative strength analysis to identify only the strongest-performing names within those groups. When the ratio falls, rotate to defensive sectors but allocate only to those exhibiting top relative strength.

## Supporting Notes

- [[N112-relative-strength-analysis-for-sector-rotation]]
- [[R249-sector-rotation-based-on-crbbond-ratio]]
- [[C340-relative-strength-analysis-for-stocks-and-sectors]]

## Connection Type

**creates_filter** — Actionability score: 5/5
