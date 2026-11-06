---
type: insight
date: 2026-10-26
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
# Exits outweigh entries: trail stops after pivot signals

## Discovery Summary

Murphy's insight that exits matter more than entries is operationalized by RG023-pf-trailing-stop-adjustment and C245-stop-order. EN071-pivot-point-buy-signal-rules provides the entry trigger, but the trader's real edge comes from the subsequent exit management — specifically placing a stop-order and trailing it according to RG023. This sequence makes the pivot signal merely the start of the trade, with stop placement governing final performance.

## Trading Implication

Traders should treat pivot-point buy signals as entry triggers, then immediately focus on stop-order placement and trailing adjustments per RG023 rather than seeking better entry precision. Prioritize exit rule design and execution over entry optimization.

## Supporting Notes

- [[RG023-pf-trailing-stop-adjustment]]
- [[C245-stop-order]]
- [[EN071-pivot-point-buy-signal-rules]]

## Connection Type

**reveals_sequence** — Actionability score: 3/5

## Related Notes
- [[INS-2026-10-10-exits-matter-trail-stops-after-pivot-point-buy-signals|Exits matter: trail stops after pivot-point buy signals]]
- [[INS-2026-10-27-exits-matter-more-stop-placement-rules-edge|Exits matter more: stop placement rules edge]]
- [[EN071-pivot-point-buy-signal-rules|Pivot Point Buy Signal Rules]]
