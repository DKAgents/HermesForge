---
type: insight
date: 2026-08-05
actionability: 3
connection_type: adds_condition
domains: [edge-conditions, indicators, rules]
sources: ["N039-double-crossover-method-10-and-50-day-combination-for-stocks", "E020-double-crossover-reduces-whipsaws-vs-single-average", "EN028-10-and-50-day-moving-average-crossover"]
seed_id: diversification_position_limit
tags: [insight, discovery, knowledge-evolution]
topic: knowledge
confidence: high
has_quotes: false
source: unknown
---
# Whipsaw Reduction via Double Crossover Affects Position Sizing Frequency

## Discovery Summary

E020-double-crossover-reduces-whipsaws states the 10/50 double crossover produces fewer but later signals than a single MA. Combined with N039 and EN028 defining the 10/50 crossover rules, this means signal frequency is lower, which directly affects how often the 1% position sizing rule (HermesForge) is triggered. Fewer whipsaws mean fewer false entries, so the 1% risk-per-trade rule is applied to higher-quality signals on average, improving the risk-adjusted return per trade without changing the rule itself.

## Trading Implication

A trader using the 10/50 double crossover with 1% position sizing should expect fewer total trades than a single-MA system, so they should not widen stops or increase position size to compensate for reduced activity — the lower frequency is a feature, not a bug.

## Supporting Notes

- [[N039-double-crossover-method-10-and-50-day-combination-for-stocks]]
- [[E020-double-crossover-reduces-whipsaws-vs-single-average]]
- [[EN028-10-and-50-day-moving-average-crossover]]

## Connection Type

**adds_condition** — Actionability score: 3/5
