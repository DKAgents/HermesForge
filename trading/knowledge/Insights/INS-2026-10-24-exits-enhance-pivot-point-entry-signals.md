---
type: insight
date: 2026-10-24
actionability: 3
connection_type: confirms_risk_rule
domains: [concepts, risk-guidelines, rules]
sources: ["RG023-pf-trailing-stop-adjustment", "C245-stop-order", "EN071-pivot-point-buy-signal-rules"]
seed_id: system_exit_design
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# Exits enhance pivot point entry signals

## Discovery Summary

EN071 (pivot-point-buy-signal-rules) provides an entry trigger, but RG023 (pf-trailing-stop-adjustment) and C245 (stop-order) together emphasize that exit management via trailing stops is critical. Murphy's insight that exits matter more than entries directly supports prioritizing stop adjustment over the entry signal itself.

## Trading Implication

After taking a pivot point buy signal, immediately apply a trailing stop adjustment from RG023 rather than setting a fixed stop, ensuring the exit adapts to price movement.

## Supporting Notes

- [[RG023-pf-trailing-stop-adjustment]]
- [[C245-stop-order]]
- [[EN071-pivot-point-buy-signal-rules]]

## Connection Type

**confirms_risk_rule** — Actionability score: 3/5

## Related Notes
- [[INS-2026-10-27-exits-matter-more-stop-placement-rules-edge|Exits matter more: stop placement rules edge]]
- [[RG023-pf-trailing-stop-adjustment|P&F Trailing Stop Adjustment]]
- [[EN071-pivot-point-buy-signal-rules|Pivot Point Buy Signal Rules]]
