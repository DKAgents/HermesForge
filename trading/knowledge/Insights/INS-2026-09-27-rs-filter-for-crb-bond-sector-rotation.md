---
type: insight
date: 2026-09-27
actionability: 4
connection_type: adds_condition
domains: [concepts, indicators, rules]
sources: ["N112-relative-strength-analysis-for-sector-rotation", "R249-sector-rotation-based-on-crbbond-ratio", "C340-relative-strength-analysis-for-stocks-and-sectors"]
seed_id: intermarket_sector_rotation
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# RS filter for CRB/Bond sector rotation

## Discovery Summary

R249 provides a rule to rotate into inflation-sensitive sectors (gold, oil, cyclicals) when the CRB/Bond ratio rises, and into defensive sectors when it falls. N112 and C340 describe using relative strength to identify outperforming sectors. Combining them creates a filter: only rotate into the inflation-sensitive sectors that show strong relative strength, and into defensive sectors that are outperforming, avoiding weak sectors within the recommended group. This improves the timing and selection of sector rotation.

## Trading Implication

When the CRB/Bond ratio signals a rotation, use relative strength ranking to select only the strongest sectors within the recommended category (e.g., top quartile by RS), rather than buying all sectors in that group.

## Supporting Notes

- [[N112-relative-strength-analysis-for-sector-rotation]]
- [[R249-sector-rotation-based-on-crbbond-ratio]]
- [[C340-relative-strength-analysis-for-stocks-and-sectors]]

## Connection Type

**adds_condition** — Actionability score: 4/5
