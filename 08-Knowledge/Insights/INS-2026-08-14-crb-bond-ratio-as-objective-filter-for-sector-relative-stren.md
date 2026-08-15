---
type: insight
date: 2026-08-14
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
# CRB/Bond Ratio as Objective Filter for Sector Relative Strength

## Discovery Summary

R249 provides a specific, quantifiable intermarket signal (rising vs. falling CRB/Bond ratio) that tells investors WHICH sector category to favor, while N112 and C340 provide the relative strength methodology to identify the BEST individual stocks or sub-sectors within that category. The combination resolves a common weakness in pure relative strength analysis: it can chase recent winners without macro context. By first filtering sector direction via the CRB/Bond ratio (R249), then applying relative strength ranking (N112, C340) within the confirmed category, traders get both macro alignment and micro precision.

## Trading Implication

When CRB/Bond ratio is rising, run relative strength screens exclusively on inflation-sensitive sectors (energy, materials, gold miners) to rank individual names; when ratio is falling, restrict relative strength screening to utilities, financials, and consumer staples — avoiding any cross-category positions regardless of short-term price strength.

## Supporting Notes

- [[N112-relative-strength-analysis-for-sector-rotation]]
- [[R249-sector-rotation-based-on-crbbond-ratio]]
- [[C340-relative-strength-analysis-for-stocks-and-sectors]]

## Connection Type

**creates_filter** — Actionability score: 4/5
