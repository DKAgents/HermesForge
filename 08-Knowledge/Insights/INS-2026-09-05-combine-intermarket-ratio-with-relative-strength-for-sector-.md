---
type: insight
date: 2026-09-05
actionability: 4
connection_type: creates_filter
domains: [concepts, indicators, rules]
sources: ["N112-relative-strength-analysis-for-sector-rotation", "R249-sector-rotation-based-on-crbbond-ratio", "C340-relative-strength-analysis-for-stocks-and-sectors"]
seed_id: intermarket_sector_rotation
tags: [insight, discovery, knowledge-evolution]
---

# Combine Intermarket Ratio with Relative Strength for Sector Timing

## Discovery Summary

The CRB/Bond ratio from R249 provides a macro-level signal for whether to favor inflation-sensitive or defensive sectors. Relative strength analysis from N112 and C340 offers a micro-level tool to identify which specific sectors or stocks within those broad categories are actually outperforming. By requiring both signals to align—e.g., a rising CRB/Bond ratio AND positive relative strength in energy or materials—traders create a filtered entry condition that avoids premature rotation into sectors not yet showing price confirmation.

## Trading Implication

When the CRB/Bond ratio indicates an inflationary regime, only rotate into inflation-sensitive sectors if their relative strength versus the broad market is also rising. Ignore sectors that 'should' benefit if price is not confirming.

## Supporting Notes

- [[N112-relative-strength-analysis-for-sector-rotation]]
- [[R249-sector-rotation-based-on-crbbond-ratio]]
- [[C340-relative-strength-analysis-for-stocks-and-sectors]]

## Connection Type

**creates_filter** — Actionability score: 4/5
