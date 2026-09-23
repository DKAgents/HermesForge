---
type: insight
date: 2026-09-22
actionability: 3
connection_type: adds_condition
domains: [concepts, risk-guidelines, rules]
sources: ["RG023-pf-trailing-stop-adjustment", "C245-stop-order", "EN071-pivot-point-buy-signal-rules"]
seed_id: system_exit_design
tags: [insight, discovery, knowledge-evolution]
topic: knowledge
confidence: high
has_quotes: false
source: unknown
---
# Trailing stops enhance pivot point exits

## Discovery Summary

EN071's pivot point buy signal uses a fixed protective stop below the current day's low, which may be too static. RG023's P&F trailing stop method—raising the stop to just below the latest o column in an uptrend—suggests an improvement: trail the stop upward as the trade progresses (e.g., to below each new minor swing low). This directly applies Murphy's insight that exits matter more than entries, as noted in C245's discussion of stop orders. Combining the rules allows a trader to lock in profits while staying in the trend.

## Trading Implication

After a pivot point buy stop is triggered, do not keep the stop at the initial level; instead, trail it upward using recent swing lows (like the latest pullback column in P&F) to protect accumulated gains.

## Supporting Notes

- [[RG023-pf-trailing-stop-adjustment]]
- [[C245-stop-order]]
- [[EN071-pivot-point-buy-signal-rules]]

## Connection Type

**adds_condition** — Actionability score: 3/5

## Related Notes
- [[C245-stop-order|Stop Order]]
- [[EN071-pivot-point-buy-signal-rules|Pivot Point Buy Signal Rules]]
