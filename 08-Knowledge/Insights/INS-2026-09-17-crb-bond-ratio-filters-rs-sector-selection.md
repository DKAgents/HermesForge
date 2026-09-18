---
type: insight
date: 2026-09-17
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
# CRB/Bond Ratio Filters RS Sector Selection

## Discovery Summary

R249-sector-rotation-based-on-crbbond-ratio provides the macro regime (rising/falling CRB/Bond ratio) that dictates which sectors to favor, while N112-relative-strength-analysis-for-sector-rotation and C340-relative-strength-analysis-for-stocks-and-sectors identify the strongest candidates within those favored groups. The connection is non-obvious: the CRB/Bond ratio acts as a filter that determines the universe of sectors, and relative strength refines the timing and selection within that universe, preventing buying strong sectors that are in the wrong macro regime.

## Trading Implication

Traders should first check the CRB/Bond ratio direction to identify the broad sector group (inflation-sensitive vs. defensive), then apply relative strength analysis to select the strongest sector/stock within that group. This combines regime alignment with momentum, avoiding long-only relative strength picks that fight the macro trend.

## Supporting Notes

- [[N112-relative-strength-analysis-for-sector-rotation]]
- [[R249-sector-rotation-based-on-crbbond-ratio]]
- [[C340-relative-strength-analysis-for-stocks-and-sectors]]

## Connection Type

**adds_condition** — Actionability score: 4/5
