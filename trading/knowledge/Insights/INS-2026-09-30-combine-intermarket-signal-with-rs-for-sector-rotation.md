---
type: insight
date: 2026-09-30
actionability: 3
connection_type: adds_condition
domains: [indicators, rules]
sources: ["N112-relative-strength-analysis-for-sector-rotation", "R249-sector-rotation-based-on-crbbond-ratio"]
seed_id: intermarket_sector_rotation
tags: [insight, discovery, knowledge-evolution]
---

# Combine intermarket signal with RS for sector rotation

## Discovery Summary

N112 focuses on using relative strength to identify sector rotation momentum, while R249 introduces the CRB/bond ratio as an intermarket trigger. Together, they suggest that relative strength rankings should be filtered or confirmed by the direction of the CRB/bond ratio, adding a macro condition to the sector allocation decision.

## Trading Implication

A trader should first rank sectors by relative strength, then only rotate into top-ranked sectors when the CRB/bond ratio confirms the expected economic regime (e.g., rising ratio favors cyclicals, falling ratio favors defensives).

## Supporting Notes

- [[N112-relative-strength-analysis-for-sector-rotation]]
- [[R249-sector-rotation-based-on-crbbond-ratio]]

## Connection Type

**adds_condition** — Actionability score: 3/5
