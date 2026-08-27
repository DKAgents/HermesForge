---
type: insight
date: 2026-08-27
actionability: 4
connection_type: creates_filter
domains: [concepts, indicators, rules]
sources: ["N112-relative-strength-analysis-for-sector-rotation", "R249-sector-rotation-based-on-crbbond-ratio", "C340-relative-strength-analysis-for-stocks-and-sectors"]
seed_id: intermarket_sector_rotation
tags: [insight, discovery, knowledge-evolution]
---

# Filter intermarket rotation with relative strength for sector selection

## Discovery Summary

R249 defines sector rotation based on the CRB/Bond ratio trend, moving into inflation-sensitive sectors (golds, oils, cyclicals) on a rising ratio and defensive sectors (utilities, financials, staples) on a falling one. N112 and C340 describe relative strength analysis as a method to identify outperforming stocks or sectors versus benchmarks. Combining these allows a trader to use the intermarket signal for broad sector allocation, then apply relative strength to select only the strongest-performing stocks or sub-sectors within that allocation, creating a confluent filter.

## Trading Implication

When the CRB/Bond ratio signals a shift into inflation-sensitive or defensive sectors, use relative strength rankings to overweight only the top-performing stocks or industry groups within the favored sector basket and avoid laggards.

## Supporting Notes

- [[N112-relative-strength-analysis-for-sector-rotation]]
- [[R249-sector-rotation-based-on-crbbond-ratio]]
- [[C340-relative-strength-analysis-for-stocks-and-sectors]]

## Connection Type

**creates_filter** — Actionability score: 4/5
