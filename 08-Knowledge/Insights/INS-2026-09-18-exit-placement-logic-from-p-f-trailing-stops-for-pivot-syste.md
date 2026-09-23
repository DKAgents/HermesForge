---
type: insight
date: 2026-09-18
actionability: 4
connection_type: resolves_conflict
domains: [concepts, risk-guidelines, rules]
sources: ["RG023-pf-trailing-stop-adjustment", "C245-stop-order", "EN071-pivot-point-buy-signal-rules"]
seed_id: system_exit_design
tags: [insight, discovery, knowledge-evolution]
topic: knowledge
confidence: high
has_quotes: false
source: unknown
---
# Exit placement logic from P&F trailing stops for pivot systems

## Discovery Summary

P&F trailing stop adjustment (RG023) provides a dynamic method to raise protective stops based on column structure, directly addressing Murphy's insight that exits matter more than entries. The Pivot Point Buy Signal Rules (EN071) define static stop placements (below current day's low or under today's open), which can be refined by applying the P&F trailing stop logic to trail the stop upward as new buy signals occur, ensuring profit protection without prematurely exiting. This resolves the conflict between rule-based static stops and the need for trend-following exit flexibility.

## Trading Implication

Trader should overlay P&F trailing stop methodology onto pivot point systems: after each buy stop is elected, trail the protective sell stop to just below the latest o column on a P&F chart, rather than relying solely on the static day's low or open.

## Supporting Notes

- [[RG023-pf-trailing-stop-adjustment]]
- [[C245-stop-order]]
- [[EN071-pivot-point-buy-signal-rules]]

## Connection Type

**resolves_conflict** — Actionability score: 4/5

## Related Notes
- [[RG023-pf-trailing-stop-adjustment|P&F Trailing Stop Adjustment]]
- [[EN071-pivot-point-buy-signal-rules|Pivot Point Buy Signal Rules]]
