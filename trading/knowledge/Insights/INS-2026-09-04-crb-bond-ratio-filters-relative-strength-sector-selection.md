---
type: insight
date: 2026-09-04
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
# CRB/Bond Ratio Filters Relative Strength Sector Selection

## Discovery Summary

The CRB/Bond ratio trend (R249) provides a macro-level signal that splits the market into inflation-sensitive sectors (golds, oils, cyclicals) or defensive sectors (utilities, financials, consumer staples). Relative strength analysis (N112, C340) can then be applied within that selected group to rank and pick the strongest stocks or subsectors. The connection is that the rotation rule defines the eligible universe, while relative strength refines the selection within it, creating a two-stage filter: first intermarket bias, then momentum-based ranking.

## Trading Implication

First determine the CRB/Bond ratio direction; if rising, scan inflation-sensitive sectors with relative strength and buy the top-ranked ones; if falling, rank defensive sectors via relative strength and buy the leaders. This targets outperformance within the regime-favored group.

## Supporting Notes

- [[N112-relative-strength-analysis-for-sector-rotation]]
- [[R249-sector-rotation-based-on-crbbond-ratio]]
- [[C340-relative-strength-analysis-for-stocks-and-sectors]]

## Connection Type

**adds_condition** — Actionability score: 4/5
