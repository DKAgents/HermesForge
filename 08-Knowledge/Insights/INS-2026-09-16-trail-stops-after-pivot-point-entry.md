---
type: insight
date: 2026-09-16
actionability: 3
connection_type: adds_condition
domains: [indicators, patterns, risk-guidelines, trading-rules]
sources: ["RG023-pf-trailing-stop-adjustment", "C245-stop-order", "EN071-pivot-point-buy-signal-rules"]
seed_id: system_exit_design
tags: [insight, discovery, knowledge-evolution]
topic: knowledge
confidence: high
has_quotes: false
source: unknown
---
# Trail Stops After Pivot Point Entry

## Discovery Summary

The pivot point buy signal rules (EN071) define an initial protective stop but lack a trailing mechanism. The P&F trailing stop adjustment (RG023) provides a method to trail stops as trends continue. Combining these, after a pivot point buy is triggered, the trader should trail the protective stop upward using the most recent pullback low (analogous to the latest o column in an uptrend). This implements Murphy's insight (C245) that exits matter more than entries by dynamically protecting profits.

## Trading Implication

After a pivot point buy signal executes, do not keep the stop fixed at the initial day's low; instead, trail the protective sell stop to just below the most recent significant pullback low as price advances.

## Supporting Notes

- [[RG023-pf-trailing-stop-adjustment]]
- [[C245-stop-order]]
- [[EN071-pivot-point-buy-signal-rules]]

## Connection Type

**adds_condition** — Actionability score: 3/5

## Related Notes
- [[RG023-pf-trailing-stop-adjustment|P&F Trailing Stop Adjustment]]
- [[EN071-pivot-point-buy-signal-rules|Pivot Point Buy Signal Rules]]
