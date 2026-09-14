---
type: insight
date: 2026-09-14
actionability: 3
connection_type: adds_condition
domains: [concepts, risk-guidelines, rules]
sources: ["C245-stop-order", "RG035-combining-technical-factors-with-money-management-for-stop-p", "EN071-pivot-point-buy-signal-rules"]
seed_id: prior_swing_low_stop
tags: [insight, discovery, knowledge-evolution]
---

# Pivot Stop Rules vs Risk Management Conflict

## Discovery Summary

The pivot point buy signal rules (EN071) require a protective sell stop below the current day's low (or today's open). The risk guideline (RG035) insists that stops be placed at valid technical levels while also respecting money management limits (max 5% risk). Conflict occurs when the distance from entry to the pivot point stop is too large for the account's risk tolerance, forcing a position size that may be too small or violating risk limits.

## Trading Implication

Before executing a pivot point signal, calculate the stop distance and adjust position size to cap loss at the maximum risk; if the stop is too wide, skip the trade or use the tighter alternative stop (below today's open) if technically valid.

## Supporting Notes

- [[C245-stop-order]]
- [[RG035-combining-technical-factors-with-money-management-for-stop-p]]
- [[EN071-pivot-point-buy-signal-rules]]

## Connection Type

**adds_condition** — Actionability score: 3/5
