---
type: insight
date: 2026-09-11
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
# Layer RS on CRB/Bond signals for sector entry timing

## Discovery Summary

R249 provides a macro regime filter using the CRB/Bond ratio to determine which sector categories to favor (inflation-sensitive vs. defensive), while N112 and C340 describe relative strength analysis for identifying outperforming sectors and stocks. By combining these, a trader can first use the CRB/Bond ratio to narrow the eligible sector universe, then apply relative strength rankings within that subset to select only those sectors that are both macro-aligned and technically outperforming.

## Trading Implication

When the CRB/Bond ratio is rising, scan only inflation-sensitive sectors (golds, oils, cyclicals) and buy those with the highest relative strength versus the broad market; when falling, scan only defensives (utilities, financials, staples) and buy the RS leaders within that group.

## Supporting Notes

- [[N112-relative-strength-analysis-for-sector-rotation]]
- [[R249-sector-rotation-based-on-crbbond-ratio]]
- [[C340-relative-strength-analysis-for-stocks-and-sectors]]

## Connection Type

**creates_filter** — Actionability score: 4/5
