---
type: insight
date: 2026-09-01
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
# Macro Bias with Relative Strength Stock Selection

## Discovery Summary

R249 describes a sector rotation rule based on the CRB/Bond ratio: buy inflation-sensitive sectors (golds, oils, cyclicals) when the ratio rises, and defensive sectors (utilities, financials, staples) when it falls. N112 and C340 explain relative strength analysis as a tool to identify outperforming stocks and sectors. Combining these, a trader can use the CRB/Bond ratio to determine the favored macro sector group, then apply relative strength analysis within that group to select the strongest individual stocks—adding a performance filter to the macro rotation rule.

## Trading Implication

First, determine the trend of the CRB/Bond ratio. If rising, run relative strength analysis on gold, oil, and cyclical stocks to buy the leaders; if falling, run relative strength on utilities, financials, and consumer staples to buy the leaders.

## Supporting Notes

- [[N112-relative-strength-analysis-for-sector-rotation]]
- [[R249-sector-rotation-based-on-crbbond-ratio]]
- [[C340-relative-strength-analysis-for-stocks-and-sectors]]

## Connection Type

**adds_condition** — Actionability score: 4/5
