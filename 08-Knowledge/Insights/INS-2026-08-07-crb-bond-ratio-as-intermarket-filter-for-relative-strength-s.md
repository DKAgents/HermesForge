---
type: insight
date: 2026-08-07
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
# CRB/Bond Ratio as Intermarket Filter for Relative Strength Sector Rotation

## Discovery Summary

R249 provides a specific intermarket signal (CRB/Bond ratio direction) that acts as a macro filter determining which sectors to apply relative strength analysis toward. N112 and C340 establish relative strength as the tool for identifying outperformers, but neither specifies which universe to scan. By combining these, traders first consult the CRB/Bond ratio direction (R249) to define the correct sector universe — inflation-sensitive vs. defensive — then apply relative strength analysis (N112, C340) within that universe to select the strongest individual names or subsectors.

## Trading Implication

When CRB/Bond ratio is rising, run relative strength screens exclusively against gold, oil, and cyclical sectors to pick the strongest names; when the ratio is falling, shift the relative strength scan to utilities, financials, and consumer staples only.

## Supporting Notes

- [[N112-relative-strength-analysis-for-sector-rotation]]
- [[R249-sector-rotation-based-on-crbbond-ratio]]
- [[C340-relative-strength-analysis-for-stocks-and-sectors]]

## Connection Type

**creates_filter** — Actionability score: 4/5
