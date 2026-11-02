---
type: insight
date: 2026-10-25
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
# Prioritize trailing stop over pivot entry

## Discovery Summary

Murphy's insight emphasizes exits over entries, connecting RG023 trailing stop adjustment and EN071 pivot point buy signal rules. Traders should integrate trailing stops based on pivot levels rather than solely optimizing entry signals, as stop placement (C245) more directly impacts performance.

## Trading Implication

Allocate more backtesting effort to trailing stop parameters (e.g., distance from pivot) than to refining pivot point entry triggers.

## Supporting Notes

- [[RG023-pf-trailing-stop-adjustment]]
- [[C245-stop-order]]
- [[EN071-pivot-point-buy-signal-rules]]

## Connection Type

**reveals_sequence** — Actionability score: 4/5

## Related Notes
- [[INS-2026-10-10-exits-matter-trail-stops-after-pivot-point-buy-signals|Exits matter: trail stops after pivot-point buy signals]]
- [[RG023-pf-trailing-stop-adjustment|P&F Trailing Stop Adjustment]]
- [[EN071-pivot-point-buy-signal-rules|Pivot Point Buy Signal Rules]]
