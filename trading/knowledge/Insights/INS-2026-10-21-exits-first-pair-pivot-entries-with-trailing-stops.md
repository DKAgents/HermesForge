---
type: insight
date: 2026-10-21
actionability: 3
connection_type: reveals_sequence
domains: [concepts, risk-guidelines, rules]
sources: ["RG023-pf-trailing-stop-adjustment", "C245-stop-order", "EN071-pivot-point-buy-signal-rules"]
seed_id: system_exit_design
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# Exits First: Pair Pivot Entries with Trailing Stops

## Discovery Summary

Murphy's insight that exits matter more than entries reframes EN071 pivot-point buy signal rules as merely entry triggers. The decisive performance driver is the exit logic in RG023-pf-trailing-stop-adjustment, executed mechanically through a C245 stop-order. The non-obvious sequence is to define and place the stop before or immediately when the pivot-point buy signal fires, rather than treating the entry signal as the primary decision.

## Trading Implication

A trader should pre-specify stop and trailing-stop adjustments using C245 stop-orders whenever EN071 pivot-point signals occur, and treat adherence to RG023 as more important than further entry optimization.

## Supporting Notes

- [[RG023-pf-trailing-stop-adjustment]]
- [[C245-stop-order]]
- [[EN071-pivot-point-buy-signal-rules]]

## Connection Type

**reveals_sequence** — Actionability score: 3/5

## Related Notes
- [[INS-2026-10-27-exits-matter-more-stop-placement-rules-edge|Exits matter more: stop placement rules edge]]
- [[EN071-pivot-point-buy-signal-rules|Pivot Point Buy Signal Rules]]
