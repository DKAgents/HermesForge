---
type: insight
date: 2026-10-28
actionability: 4
connection_type: adds_condition
domains: [concepts, risk-guidelines, rules]
sources: ["RG023-pf-trailing-stop-adjustment", "C245-stop-order", "EN071-pivot-point-buy-signal-rules"]
seed_id: system_exit_design
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# Exit discipline via pivot stop placement

## Discovery Summary

RG023's trailing-stop adjustment rule combined with EN071's pivot-point buy signal rules creates a specific stop-loss placement condition: when a pivot-point buy signal triggers, the stop should be placed below the pivot low (not a fixed dollar amount) and then trailed per RG023 as price advances. This connects Murphy's insight that exits matter more than entries by forcing the trader to define the exit (stop) at the moment of entry, using the pivot structure as a concrete stop level.

## Trading Implication

When a pivot-point buy signal fires per EN071, immediately set the stop loss at the pivot low (using C245 stop-order type) and apply RG023's trailing adjustment as the trade moves in profit.

## Supporting Notes

- [[RG023-pf-trailing-stop-adjustment]]
- [[C245-stop-order]]
- [[EN071-pivot-point-buy-signal-rules]]

## Connection Type

**adds_condition** — Actionability score: 4/5
