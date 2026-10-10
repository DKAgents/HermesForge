---
type: insight
date: 2026-10-10
actionability: 3
connection_type: confirms_risk_rule
domains: [concepts, risk-guidelines, rules]
sources: ["RG023-pf-trailing-stop-adjustment", "C245-stop-order", "EN071-pivot-point-buy-signal-rules"]
seed_id: system_exit_design
tags: [insight, discovery, knowledge-evolution]
---

# Exits matter: trail stops after pivot-point buy signals

## Discovery Summary

Murphy's insight that exits matter more than entries directly supports RG023-pf-trailing-stop-adjustment: the outcome of a trade is driven by how the exit is managed, not just by the entry trigger. EN071-pivot-point-buy-signal-rules provides the entry setup, while C245-stop-order gives the execution mechanism to enforce a disciplined exit. Therefore, EN071 buy signals should be coupled with explicit trailing-stop adjustment rules from the outset rather than treated as standalone signals.

## Trading Implication

For every EN071 pivot-point buy signal, predefine a C245 stop order and trail it according to RG023 before entering; treat exit management as the primary driver of performance.

## Supporting Notes

- [[RG023-pf-trailing-stop-adjustment]]
- [[C245-stop-order]]
- [[EN071-pivot-point-buy-signal-rules]]

## Connection Type

**confirms_risk_rule** — Actionability score: 3/5
