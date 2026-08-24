---
type: insight
date: 2026-08-23
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

R249 provides a concrete intermarket signal (CRB/Bond ratio direction) that tells traders WHICH sectors to favor, while N112 and C340 provide the analytical tool (relative strength analysis) to rank and select the best individual stocks or ETFs within those favored sectors. The combination resolves a common gap: intermarket analysis tells you where to rotate, but relative strength analysis tells you exactly which names within that rotation to buy. Rising CRB/Bond ratio → screen inflation-sensitive sectors (golds, oils, cyclicals) using relative strength to find the strongest individual positions; falling ratio → screen defensives (utilities, financials, consumer staples) using relative strength to rank the top candidates.

## Trading Implication

A trader should first check the CRB/Bond ratio direction to determine the correct sector universe, then apply relative strength analysis within that universe to select only the top-ranked stocks or ETFs for capital allocation — avoiding stocks in the correct sector but with weak relative strength.

## Supporting Notes

- [[N112-relative-strength-analysis-for-sector-rotation]]
- [[R249-sector-rotation-based-on-crbbond-ratio]]
- [[C340-relative-strength-analysis-for-stocks-and-sectors]]

## Connection Type

**creates_filter** — Actionability score: 4/5
