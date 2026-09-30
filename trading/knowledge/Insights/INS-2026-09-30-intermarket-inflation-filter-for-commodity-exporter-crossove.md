---
type: insight
date: 2026-09-30
actionability: 4
connection_type: creates_filter
domains: [edge-conditions, indicators, intermarket analysis, rules]
sources: ["N039-double-crossover-method-10-and-50-day-combination-for-stocks", "E040-commodity-exporters-and-deflation-risk", "R310-adjusting-long-term-charts-for-inflation"]
seed_id: commodity_inflation_stock
tags: [insight, discovery, knowledge-evolution]
---

# Intermarket inflation filter for commodity-exporter crossovers

## Discovery Summary

N039's 10/50-day crossover is a nominal-price trend signal, but E040 warns that commodity exporters carry deflation risk when commodity prices decline. R310 adds that long-term charts should be inflation-adjusted, since nominal price levels can mask real losses. Applying Murphy's commodities → bonds → stocks chain makes commodity direction a leading filter for crossover signals in commodity-exporter equities.

## Trading Implication

For commodity-exporter stocks, only take bullish N039 crossovers when the underlying commodity trend is also rising and the long-term inflation-adjusted chart supports the uptrend; bearish crossovers are more reliable when commodity prices and real trend are weak.

## Supporting Notes

- [[N039-double-crossover-method-10-and-50-day-combination-for-stocks]]
- [[E040-commodity-exporters-and-deflation-risk]]
- [[R310-adjusting-long-term-charts-for-inflation]]

## Connection Type

**creates_filter** — Actionability score: 4/5
