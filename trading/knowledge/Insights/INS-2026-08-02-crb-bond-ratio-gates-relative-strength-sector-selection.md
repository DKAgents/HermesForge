---
type: insight
date: 2026-08-02
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
# CRB/Bond Ratio Gates Relative Strength Sector Selection

## Discovery Summary

R249 provides a macro intermarket signal (CRB/Bond ratio direction) that determines WHICH sectors to apply relative strength analysis toward. N112 and C340 describe relative strength as a tool for identifying outperformers, but offer no guidance on which sector universe to screen. By combining them, the CRB/Bond ratio acts as a first-stage filter: rising ratio directs relative strength screening to inflation-sensitive sectors (golds, oils, cyclicals); falling ratio directs screening to defensives (utilities, financials, consumer staples). This creates a two-stage decision process not explicitly described in any single note.

## Trading Implication

A trader should first check CRB/Bond ratio trend to determine the relevant sector universe, then apply relative strength analysis within that universe to select the strongest individual sectors or stocks — avoiding applying relative strength indiscriminately across all sectors regardless of macro regime.

## Supporting Notes

- [[N112-relative-strength-analysis-for-sector-rotation]]
- [[R249-sector-rotation-based-on-crbbond-ratio]]
- [[C340-relative-strength-analysis-for-stocks-and-sectors]]

## Connection Type

**creates_filter** — Actionability score: 4/5
