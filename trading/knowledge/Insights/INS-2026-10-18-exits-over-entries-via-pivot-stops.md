---
type: insight
date: 2026-10-18
actionability: 4
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
# Exits over entries via pivot stops

## Discovery Summary

The seed question references Murphy's insight that exits matter more than entries. This connects EN071-pivot-point-buy-signal-rules (entry) with RG023-pf-trailing-stop-adjustment (exit) via C245-stop-order (mechanism). The non-obvious link is that the value of pivot point buy signals is realized only when followed by disciplined trailing stop adjustments, making exit management the primary driver of performance.

## Trading Implication

Traders should use pivot point buy signals only as entry triggers, then immediately apply a trailing stop adjustment rule from RG023 to manage the exit, prioritizing stop placement over entry timing.

## Supporting Notes

- [[RG023-pf-trailing-stop-adjustment]]
- [[C245-stop-order]]
- [[EN071-pivot-point-buy-signal-rules]]

## Connection Type

**reveals_sequence** — Actionability score: 4/5

## Related Notes
- [[INS-2026-10-10-exits-matter-trail-stops-after-pivot-point-buy-signals|Exits matter: trail stops after pivot-point buy signals]]
- [[INS-2026-10-27-exits-matter-more-stop-placement-rules-edge|Exits matter more: stop placement rules edge]]
- [[RG023-pf-trailing-stop-adjustment|P&F Trailing Stop Adjustment]]
- [[EN071-pivot-point-buy-signal-rules|Pivot Point Buy Signal Rules]]
