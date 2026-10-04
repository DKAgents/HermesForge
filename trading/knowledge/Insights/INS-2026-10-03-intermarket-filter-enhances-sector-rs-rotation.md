---
type: insight
date: 2026-10-03
actionability: 4
connection_type: adds_condition
domains: [indicators, intermarket analysis, rules, sector rotation]
sources: ["N112-relative-strength-analysis-for-sector-rotation", "R249-sector-rotation-based-on-crbbond-ratio"]
seed_id: intermarket_sector_rotation
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# Intermarket Filter Enhances Sector RS Rotation

## Discovery Summary

R249 uses the CRB/bond ratio as an intermarket signal to drive sector rotation, while N112 focuses on relative strength (RS) analysis for the same purpose. Combining them adds a conditioning step: first determine the market regime via the CRB/bond ratio (e.g., rising ratio favors commodities/cyclicals), then apply RS analysis within that regime to select the strongest sectors, creating a more robust, systematic rotation strategy.

## Trading Implication

Traders should first check the trend of the CRB/bond ratio to set the macro bias (risk-on vs risk-off), then rank sectors by relative strength only within the favored group to avoid counter-trend picks.

## Supporting Notes

- [[N112-relative-strength-analysis-for-sector-rotation]]
- [[R249-sector-rotation-based-on-crbbond-ratio]]

## Connection Type

**adds_condition** — Actionability score: 4/5
