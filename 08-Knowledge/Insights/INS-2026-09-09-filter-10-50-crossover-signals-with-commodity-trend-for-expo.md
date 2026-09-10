---
type: insight
date: 2026-09-09
actionability: 4
connection_type: creates_filter
domains: [edge-conditions, indicators, rules]
sources: ["N039-double-crossover-method-10-and-50-day-combination-for-stocks", "EN028-10-and-50-day-moving-average-crossover", "E040-commodity-exporters-and-deflation-risk"]
seed_id: commodity_inflation_stock
tags: [insight, discovery, knowledge-evolution]
topic: knowledge
confidence: high
has_quotes: false
source: unknown
---
# Filter 10/50 crossover signals with commodity trend for exporter stocks

## Discovery Summary

The 10/50-day moving average crossover method (N039, EN028) generates buy signals for stocks, but note E040 warns that falling commodity prices severely damage commodity-exporting nations' equity markets. Combining these, a trader can filter out 10/50 crossover buy signals on indices or ETFs of countries like Australia, Canada, Mexico, or Russia whenever commodity prices are in a downtrend, as per Murphy's intermarket sequence of commodities leading stocks.

## Trading Implication

Before acting on a 10/50-day crossover buy signal, check the trend of a broad commodity index; if commodities are declining, ignore the signal on commodity-exporting country ETFs.

## Supporting Notes

- [[N039-double-crossover-method-10-and-50-day-combination-for-stocks]]
- [[EN028-10-and-50-day-moving-average-crossover]]
- [[E040-commodity-exporters-and-deflation-risk]]

## Connection Type

**creates_filter** — Actionability score: 4/5
