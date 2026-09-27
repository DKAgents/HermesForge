---
type: insight
date: 2026-09-07
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
# Position sizing clarifies crossover signal reliability trade-off

## Discovery Summary

The double crossover method (10/50 day) is explicitly designed to reduce whipsaws at the cost of lag, as noted in E020. While this improves signal reliability over single MAs, the remaining whipsaw risk means traders should not overweight any single crossover signal—aligning with portfolio concentration limits like Murphy's 10-15% per market or HermesForge's 1% position sizing, which cap damage from false signals.

## Trading Implication

When trading the 10/50 crossover, size positions conservatively (e.g., 1% risk per trade or 10-15% max per market) because the method's lag means you will still experience some whipsaws, particularly in choppy markets.

## Supporting Notes

- [[N039-double-crossover-method-10-and-50-day-combination-for-stocks]]
- [[E020-double-crossover-reduces-whipsaws-vs-single-average]]
- [[EN028-10-and-50-day-moving-average-crossover]]

## Connection Type

**adds_condition** — Actionability score: 3/5
