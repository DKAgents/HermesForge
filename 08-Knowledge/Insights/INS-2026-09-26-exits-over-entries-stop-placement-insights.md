---
type: insight
date: 2026-09-26
actionability: 4
connection_type: confirms_risk_rule
domains: [concepts, risk-guidelines, rules]
sources: ["RG023-pf-trailing-stop-adjustment", "C245-stop-order", "EN071-pivot-point-buy-signal-rules"]
seed_id: system_exit_design
tags: [insight, discovery, knowledge-evolution]
---

# Exits over Entries: Stop Placement Insights

## Discovery Summary

Murphy's insight that exits matter more than entries is directly operationalized by the P&F trailing stop adjustment (RG023) and the pivot point buy signal rules (EN071). The former provides a systematic method to trail stops along P&F columns, while the latter defines specific protective stop levels based on daily pivot points. The stop order concept (C245) underpins both, reinforcing that disciplined exit management is critical for profitability.

## Trading Implication

Traders should prioritize mastering stop placement techniques (e.g., P&F column-based trailing or pivot point stops) over entry refinement, as these directly control risk and lock in gains.

## Supporting Notes

- [[RG023-pf-trailing-stop-adjustment]]
- [[C245-stop-order]]
- [[EN071-pivot-point-buy-signal-rules]]

## Connection Type

**confirms_risk_rule** — Actionability score: 4/5
