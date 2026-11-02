---
type: insight
date: 2026-10-22
actionability: 3
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
# Pivot entries need defined stop exits

## Discovery Summary

EN071-pivot-point-buy-signal-rules provides an entry trigger, but Murphy's principle that exits matter more than entries implies that the buy signal is incomplete without a matching exit plan. RG023-pf-trailing-stop-adjustment and C245-stop-order supply the mechanism: enter only when a stop order can be placed at a logical pivot level and then trailed according to the position management rules.

## Trading Implication

Before acting on a pivot point buy signal, require a predefined stop order below the relevant pivot and a trailing stop adjustment plan; do not treat the entry signal on its own as the trade.

## Supporting Notes

- [[RG023-pf-trailing-stop-adjustment]]
- [[C245-stop-order]]
- [[EN071-pivot-point-buy-signal-rules]]

## Connection Type

**adds_condition** — Actionability score: 3/5

## Related Notes
- [[INS-2026-10-10-exits-matter-trail-stops-after-pivot-point-buy-signals|Exits matter: trail stops after pivot-point buy signals]]
- [[INS-2026-10-27-exits-matter-more-stop-placement-rules-edge|Exits matter more: stop placement rules edge]]
- [[RG023-pf-trailing-stop-adjustment|P&F Trailing Stop Adjustment]]
- [[C245-stop-order|Stop Order]]
- [[EN071-pivot-point-buy-signal-rules|Pivot Point Buy Signal Rules]]
