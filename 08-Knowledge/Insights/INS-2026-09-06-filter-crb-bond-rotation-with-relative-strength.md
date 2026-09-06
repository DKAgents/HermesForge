---
type: insight
date: 2026-09-06
actionability: 4
connection_type: creates_filter
domains: [concepts, indicators, rules]
sources: ["N112-relative-strength-analysis-for-sector-rotation", "R249-sector-rotation-based-on-crbbond-ratio", "C340-relative-strength-analysis-for-stocks-and-sectors"]
seed_id: intermarket_sector_rotation
tags: [insight, discovery, knowledge-evolution]
---

# Filter CRB/Bond Rotation with Relative Strength

## Discovery Summary

R249 provides a macro rotation rule based on the CRB/Bond ratio: buy inflation-sensitive sectors when the ratio rises, rotate to defensives when it falls. N112 and C340 show how relative strength analysis identifies outperforming sectors. Using relative strength to filter the thematic groups from R249 can improve sector selection by avoiding laggards within the favored macro basket.

## Trading Implication

When the CRB/Bond ratio signals a shift (rising/falling), only enter sectors within the appropriate thematic group that also show strong relative strength, rather than buying the entire group.

## Supporting Notes

- [[N112-relative-strength-analysis-for-sector-rotation]]
- [[R249-sector-rotation-based-on-crbbond-ratio]]
- [[C340-relative-strength-analysis-for-stocks-and-sectors]]

## Connection Type

**creates_filter** — Actionability score: 4/5
