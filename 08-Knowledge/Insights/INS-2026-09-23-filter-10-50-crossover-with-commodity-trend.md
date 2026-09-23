---
type: insight
date: 2026-09-23
actionability: 4
connection_type: creates_filter
domains: [edge_conditions, indicators, rules]
sources: ["N039-double-crossover-method-10-and-50-day-combination-for-stocks", "EN028-10-and-50-day-moving-average-crossover", "E040-commodity-exporters-and-deflation-risk"]
seed_id: commodity_inflation_stock
tags: [insight, discovery, knowledge-evolution]
---

# Filter 10/50 crossover with commodity trend

## Discovery Summary

The double crossover method (N039 and EN028) uses 10/50 day moving averages to generate buy/sell signals for stocks. The edge condition E040 notes that falling commodity prices harm commodity-exporting countries' equity markets. Integrating Murphy's intermarket chain suggests that a decline in commodities often precedes weakness in those markets, making the bearish crossover more reliable. Therefore, traders can use commodity price trends as a leading filter to validate crossover signals in commodity-exporting country ETFs.

## Trading Implication

When trading ETFs of commodity-exporting nations (e.g., Canada, Australia), only act on 10/50 crossover sell signals if commodities are in a downtrend, and buy signals only if commodities are rising.

## Supporting Notes

- [[N039-double-crossover-method-10-and-50-day-combination-for-stocks]]
- [[EN028-10-and-50-day-moving-average-crossover]]
- [[E040-commodity-exporters-and-deflation-risk]]

## Connection Type

**creates_filter** — Actionability score: 4/5
