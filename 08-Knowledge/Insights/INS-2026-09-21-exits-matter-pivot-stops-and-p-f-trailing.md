---
type: insight
date: 2026-09-21
actionability: 3
connection_type: confirms_risk_rule
domains: [concepts, risk-guidelines, rules]
sources: ["RG023-pf-trailing-stop-adjustment", "C245-stop-order", "EN071-pivot-point-buy-signal-rules"]
seed_id: system_exit_design
tags: [insight, discovery, knowledge-evolution]
---

# Exits Matter: Pivot Stops and P&F Trailing

## Discovery Summary

Murphy's insight that exits matter more than entries is confirmed by both the pivot point buy signal rules (EN071) which specify initial stop placements, and the P&F trailing stop adjustment (RG023) which provides a method to dynamically protect profits. Together, they illustrate that disciplined stop placement—whether fixed or trailing—is the core of effective exit management, as emphasized in the stop order concept (C245).

## Trading Implication

A trader should combine an initial protective stop based on pivot point lows with a trailing stop technique (e.g., P&F columns) to lock in profits as the trend develops, prioritizing exit quality over entry precision.

## Supporting Notes

- [[RG023-pf-trailing-stop-adjustment]]
- [[C245-stop-order]]
- [[EN071-pivot-point-buy-signal-rules]]

## Connection Type

**confirms_risk_rule** — Actionability score: 3/5
