---
type: insight
date: 2026-09-20
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
# RSI Sector Strength Enhances CRB/Bond Rotation Signals

## Discovery Summary

The CRB/Bond ratio rule (R249) dictates rotating into inflation-sensitive sectors when rising and defensive sectors when falling. Adding relative strength analysis (N112, C340) allows a trader to filter these rotation signals by requiring that the target sector also demonstrate relative strength against the market, thus avoiding buying weak sectors even when the ratio suggests them. This combines a macro intermarket trigger with a micro performance filter, increasing signal reliability.

## Trading Implication

When CRB/Bond ratio turns up, only buy golds/oils/cyclicals that rank in the top relative strength quartile; when it turns down, rotate into defensive sectors (utilities, financials, staples) that show relative strength, but avoid those with lagging relative strength.

## Supporting Notes

- [[N112-relative-strength-analysis-for-sector-rotation]]
- [[R249-sector-rotation-based-on-crbbond-ratio]]
- [[C340-relative-strength-analysis-for-stocks-and-sectors]]

## Connection Type

**adds_condition** — Actionability score: 4/5
