---
type: insight
date: 2026-11-10
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
# Exits matter: pivot stops plus P&F trailing sequence

## Discovery Summary

Murphy's exit-focused insight is implemented by EN071 Pivot Point Buy Signal Rules: entry is a buy stop, but the protective sell stop below today's low immediately defines the exit risk. Once in the trade, RG023 P&F Trailing Stop Adjustment instructs trailing the stop below the latest o column as repeat buy signals occur, converting a single risk stop into a profit-protection mechanism. C245 Stop Order reminds that these stops become market orders and may fill beyond the stop price in fast markets.

## Trading Implication

Place the initial protective stop immediately after a pivot-point buy stop fills, then trail it below the latest P&F o column as the trend advances; account for possible slippage on stop fills.

## Supporting Notes

- [[RG023-pf-trailing-stop-adjustment]]
- [[C245-stop-order]]
- [[EN071-pivot-point-buy-signal-rules]]

## Connection Type

**reveals_sequence** — Actionability score: 4/5

## Related Notes
- [[RG023-pf-trailing-stop-adjustment|P&F Trailing Stop Adjustment]]
- [[C243-market-order|Market Order]]
- [[C245-stop-order|Stop Order]]
- [[EN071-pivot-point-buy-signal-rules|Pivot Point Buy Signal Rules]]
