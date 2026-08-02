---
type: insight
date: 2026-08-01
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
# CRB/Bond Ratio Triggers Relative Strength Sector Rotation Signal

## Discovery Summary

R249 provides a concrete intermarket trigger (CRB/Bond ratio direction) that tells traders WHEN to rotate, while N112 and C340 provide the methodology (relative strength analysis) for identifying WHICH specific sectors or stocks to favor within the rotation. The combination resolves a gap: relative strength analysis alone doesn't tell you which macro regime you're in, while the CRB/Bond ratio alone doesn't rank which specific inflation-sensitive or defensive stocks are strongest. Using the CRB/Bond ratio as the regime filter and relative strength as the stock/sector selection tool within that regime creates a two-stage decision process.

## Trading Implication

When the CRB/Bond ratio is rising, screen for the strongest relative strength performers within golds, oils, and cyclicals to concentrate capital; when falling, apply relative strength screening within utilities, financials, and consumer staples to rank and select the best defensive positions.

## Supporting Notes

- [[N112-relative-strength-analysis-for-sector-rotation]]
- [[R249-sector-rotation-based-on-crbbond-ratio]]
- [[C340-relative-strength-analysis-for-stocks-and-sectors]]

## Connection Type

**creates_filter** — Actionability score: 4/5
