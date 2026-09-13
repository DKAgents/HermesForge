---
type: insight
date: 2026-09-13
actionability: 4
connection_type: creates_filter
domains: [concepts, indicators, rules]
sources: ["N112-relative-strength-analysis-for-sector-rotation", "R249-sector-rotation-based-on-crbbond-ratio", "C340-relative-strength-analysis-for-stocks-and-sectors"]
seed_id: intermarket_sector_rotation
tags: [insight, discovery, knowledge-evolution]
---

# RS Filter for CRB/Bond Sector Rotation Signals

## Discovery Summary

R249 provides a macro sector rotation rule based on the CRB/Bond ratio: buy inflation-sensitive sectors when the ratio rises, rotate to defensives when it falls. N112 and C340 describe relative strength analysis to identify outperforming sectors and stocks. Combining these, a trader can use relative strength as a confirmation filter, entering only those suggested sectors that are actually showing strong relative performance versus the market.

## Trading Implication

Before acting on a CRB/Bond ratio signal, confirm that the target sector (e.g., golds, oils, cyclicals or utilities, staples) is showing positive relative strength versus the broad market; only enter if relative strength aligns with the intermarket signal.

## Supporting Notes

- [[N112-relative-strength-analysis-for-sector-rotation]]
- [[R249-sector-rotation-based-on-crbbond-ratio]]
- [[C340-relative-strength-analysis-for-stocks-and-sectors]]

## Connection Type

**creates_filter** — Actionability score: 4/5
