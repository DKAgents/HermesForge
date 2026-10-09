---
type: insight
date: 2026-10-08
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
# Exits matter: stop rules over entries

## Discovery Summary

Murphy's insight that exits matter more than entries connects to RG023-pf-trailing-stop-adjustment and EN071-pivot-point-buy-signal-rules by emphasizing that the trailing stop (from RG023) should be set based on pivot point levels from EN071, overriding any entry bias. C245-stop-order reinforces that the stop must be an actual order, not just a mental level.

## Trading Implication

Place a trailing stop order at the pivot point low before acting on a buy signal, ensuring the exit is prioritized over the entry trigger.

## Supporting Notes

- [[RG023-pf-trailing-stop-adjustment]]
- [[C245-stop-order]]
- [[EN071-pivot-point-buy-signal-rules]]

## Connection Type

**reveals_sequence** — Actionability score: 3/5

## Related Notes
- [[C245-stop-order|Stop Order]]
