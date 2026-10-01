---
type: insight
date: 2026-10-01
actionability: 3
connection_type: reveals_sequence
domains: [concepts, risk-guidelines, rules]
sources: ["RG023-pf-trailing-stop-adjustment", "C245-stop-order", "EN071-pivot-point-buy-signal-rules"]
seed_id: system_exit_design
tags: [insight, discovery, knowledge-evolution]
---

# Exit priority over entry via trailing stops

## Discovery Summary

Murphy's insight that exits matter more than entries highlights the need to couple pivot point buy signal rules (EN071) with rigorous stop management. The trailing stop adjustment guideline (RG023) provides a method to dynamically protect profits after entry, while the stop order concept (C245) defines the execution mechanism. Together, they form a sequence where entry is secondary to the trailing stop placement and adjustment process.

## Trading Implication

After executing a pivot point buy signal, immediately set a trailing stop per RG023 (e.g., at the pivot low) and adjust it systematically, focusing more on exit discipline than on refining entry signals.

## Supporting Notes

- [[RG023-pf-trailing-stop-adjustment]]
- [[C245-stop-order]]
- [[EN071-pivot-point-buy-signal-rules]]

## Connection Type

**reveals_sequence** — Actionability score: 3/5
