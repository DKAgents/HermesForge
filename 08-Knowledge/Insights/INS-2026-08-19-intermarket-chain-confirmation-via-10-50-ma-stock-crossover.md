---
type: insight
date: 2026-08-19
actionability: 3
connection_type: adds_condition
domains: [indicators, intermarket_analysis, rules]
sources: ["N039-double-crossover-method-10-and-50-day-combination-for-stocks", "EN028-10-and-50-day-moving-average-crossover"]
seed_id: commodity_inflation_stock
tags: [insight, discovery, knowledge-evolution]
---

# Intermarket Chain Confirmation via 10/50 MA Stock Crossover

## Discovery Summary

The seed question introduces Murphy's intermarket chain (commodities → bonds → stocks) as a macro sequence for position trading. Notes N039 and EN028 both describe the 10/50-day double crossover as the specific entry/exit mechanism for stocks. The non-obvious connection is that the 10/50 crossover signal in stocks becomes more reliable and higher-conviction when it aligns with the intermarket sequence — i.e., when commodity strength has already preceded bond weakness and stock strength, the 10-day crossing above the 50-day in stocks represents a late-stage confirmation rather than a premature signal. Using the crossover alone ignores upstream intermarket context.

## Trading Implication

Before acting on a 10-day crossing above the 50-day buy signal in stocks, confirm that the intermarket chain is aligned (commodities rising, bonds turning, stocks following); avoid buy signals that occur when the intermarket sequence is out of order or in conflict.

## Supporting Notes

- [[N039-double-crossover-method-10-and-50-day-combination-for-stocks]]
- [[EN028-10-and-50-day-moving-average-crossover]]

## Connection Type

**adds_condition** — Actionability score: 3/5
