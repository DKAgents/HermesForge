---
type: insight
date: 2026-09-14
actionability: 4
connection_type: adds_condition
domains: [concepts, risk-guidelines, rules]
sources: ["RG023-pf-trailing-stop-adjustment", "C245-stop-order", "EN071-pivot-point-buy-signal-rules"]
seed_id: system_exit_design
tags: [insight, discovery, knowledge-evolution]
---

# Exit rules prevent premature stop loss triggers

## Discovery Summary

Murphy's insight that exits matter more than entries is directly applied in EN071-pivot-point-buy-signal-rules, which delays trade entry until 35 minutes before close and avoids action in the first 30 minutes. This resolves a conflict with RG023-pf-trailing-stop-adjustment's trailing stop logic by ensuring stops are placed after stable price points (e.g., below current day's low or open), reducing the likelihood of being stopped out by intraday noise. C245-stop-order confirms that protective stops are critical for profit protection, but EN071's delayed entry rules give those stops a higher probability of holding.

## Trading Implication

Apply delayed entry rules (e.g., avoid first 30 minutes, wait until late in the session) when using trailing stops from RG023, so that stop levels are set on more meaningful price points and are less likely to be hit by volatile early moves.

## Supporting Notes

- [[RG023-pf-trailing-stop-adjustment]]
- [[C245-stop-order]]
- [[EN071-pivot-point-buy-signal-rules]]

## Connection Type

**adds_condition** — Actionability score: 4/5
