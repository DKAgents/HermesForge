---
type: insight
date: 2026-08-16
actionability: 3
connection_type: adds_condition
domains: [edge-conditions, indicators, rules]
sources: ["N039-double-crossover-method-10-and-50-day-combination-for-stocks", "E020-double-crossover-reduces-whipsaws-vs-single-average", "EN028-10-and-50-day-moving-average-crossover"]
seed_id: diversification_position_limit
tags: [insight, discovery, knowledge-evolution]
---

# Double Crossover Lag Creates Position Sizing Entry Timing Conflict

## Discovery Summary

E020 explicitly states that the double crossover method (10/50 MA as defined in N039 and EN028) lags the market more than a single average, producing fewer whipsaws but less timely entries. This lag means that by the time a 10/50 crossover signal fires, price has already moved meaningfully. A 1% position sizing rule (referenced in seed question) applied at the lagged crossover entry point may be entering at a worse risk-adjusted location than the rule anticipates, since the move is already partially complete and the logical stop (below the 50-day) may be proportionally farther from entry.

## Trading Implication

When using the 10/50 double crossover for entries, calculate position size using the distance from entry to the 50-day MA as the stop reference, not a fixed ATR multiple, to account for the built-in lag that widens the entry-to-stop distance versus a single-average system.

## Supporting Notes

- [[N039-double-crossover-method-10-and-50-day-combination-for-stocks]]
- [[E020-double-crossover-reduces-whipsaws-vs-single-average]]
- [[EN028-10-and-50-day-moving-average-crossover]]

## Connection Type

**adds_condition** — Actionability score: 3/5
