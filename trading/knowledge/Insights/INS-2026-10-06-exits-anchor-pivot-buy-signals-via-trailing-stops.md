---
type: insight
date: 2026-10-06
actionability: 4
connection_type: adds_condition
domains: [concepts, risk-guidelines, rules]
sources: ["RG023-pf-trailing-stop-adjustment", "C245-stop-order", "EN071-pivot-point-buy-signal-rules"]
seed_id: system_exit_design
tags: [insight, discovery, knowledge-evolution]
---

# Exits Anchor Pivot Buy Signals via Trailing Stops

## Discovery Summary

Murphy's principle that exits matter more than entries means an EN071 pivot-point buy signal is incomplete without a defined exit plan. C245-stop-order and RG023-pf-trailing-stop-adjustment provide the exit mechanism: enter on the pivot signal, then immediately place a protective stop and trail it as price moves in favor. This connects entry timing to the risk-management layer that determines actual P&L.

## Trading Implication

After a valid EN071 pivot-point buy signal, immediately place a protective stop-order and apply RG023 trailing-stop rules to lock in gains. Do not evaluate the trade solely by entry quality; manage the exit actively from the first bar.

## Supporting Notes

- [[RG023-pf-trailing-stop-adjustment]]
- [[C245-stop-order]]
- [[EN071-pivot-point-buy-signal-rules]]

## Connection Type

**adds_condition** — Actionability score: 4/5
