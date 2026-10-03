---
type: insight
date: 2026-10-02
actionability: 4
connection_type: reveals_sequence
domains: [indicators, rules]
sources: ["N112-relative-strength-analysis-for-sector-rotation", "R249-sector-rotation-based-on-crbbond-ratio"]
seed_id: intermarket_sector_rotation
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# Intermarket filter for relative strength sector rotation

## Discovery Summary

N112 provides relative strength analysis for ranking sectors, while R249 defines rotation based on the CRB/Bond ratio. Combining them creates a sequence: first use R249's intermarket signal to determine the broad sector bias (e.g., cyclical vs defensive), then apply N112's relative strength ranking to select the strongest sectors within that bias.

## Trading Implication

Monitor the CRB/Bond ratio trend (from R249) to decide the macro tilt, then use N112's relative strength metrics to pick the best-performing sectors aligned with that tilt.

## Supporting Notes

- [[N112-relative-strength-analysis-for-sector-rotation]]
- [[R249-sector-rotation-based-on-crbbond-ratio]]

## Connection Type

**reveals_sequence** — Actionability score: 4/5
