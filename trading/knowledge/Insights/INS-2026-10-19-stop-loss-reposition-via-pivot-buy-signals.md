---
type: insight
date: 2026-10-19
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
# Stop loss reposition via pivot buy signals

## Discovery Summary

EN071 defines pivot point buy signal rules, which identify entry points. C245 explains stop orders as exit mechanisms. RG023 discusses trailing stop adjustment, reinforcing Murphy's insight that exit placement (not entry) determines outcome. Together, they suggest that when a pivot buy signal triggers, the trader should immediately set a trailing stop at a calculated pivot level, not a fixed price, to lock in gains as the trade progresses.

## Trading Implication

After a pivot buy signal, place an initial stop just below the pivot low and immediately convert it to a trailing stop that moves with each new pivot high, ensuring exits are dynamically managed relative to price action.

## Supporting Notes

- [[RG023-pf-trailing-stop-adjustment]]
- [[C245-stop-order]]
- [[EN071-pivot-point-buy-signal-rules]]

## Connection Type

**adds_condition** — Actionability score: 4/5

## Related Notes
- [[INS-2026-10-10-exits-matter-trail-stops-after-pivot-point-buy-signals|Exits matter: trail stops after pivot-point buy signals]]
- [[RG023-pf-trailing-stop-adjustment|P&F Trailing Stop Adjustment]]
- [[C245-stop-order|Stop Order]]
- [[EN071-pivot-point-buy-signal-rules|Pivot Point Buy Signal Rules]]
