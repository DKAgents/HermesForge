---
type: insight
date: 2026-08-20
actionability: 3
connection_type: adds_condition
domains: [edge-conditions, indicators, risk-management, rules]
sources: ["N039-double-crossover-method-10-and-50-day-combination-for-stocks", "E020-double-crossover-reduces-whipsaws-vs-single-average", "EN028-10-and-50-day-moving-average-crossover"]
seed_id: diversification_position_limit
tags: [insight, discovery, knowledge-evolution]
---

# Double Crossover Lag Creates Position Sizing Entry Timing Gap

## Discovery Summary

E020 explicitly states the double crossover method (10/50 as specified in N039 and EN028) lags the market more than a single average, producing delayed entries and exits. This lag interacts directly with 1% position sizing rules: because the 10/50 crossover entry is already late relative to actual trend initiation, a trader using 1% fixed position sizing at the crossover signal may be entering after significant price movement has already occurred, reducing the reward-to-risk ratio on each trade. The lag effect from E020 means the effective risk per trade could be higher than the nominal 1% if stop placement must account for the delayed entry point being further from the true trend origin.

## Trading Implication

When using the 10/50 double crossover for entry signals, calculate position size based on stop distance from the crossover price, not from the trend origin — and consider reducing position size below 1% if the crossover occurs well above a natural support level, since lag has already consumed potential reward.

## Supporting Notes

- [[N039-double-crossover-method-10-and-50-day-combination-for-stocks]]
- [[E020-double-crossover-reduces-whipsaws-vs-single-average]]
- [[EN028-10-and-50-day-moving-average-crossover]]

## Connection Type

**adds_condition** — Actionability score: 3/5
