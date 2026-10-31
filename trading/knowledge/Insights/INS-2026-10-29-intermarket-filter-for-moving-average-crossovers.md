---
type: insight
date: 2026-10-29
actionability: 4
connection_type: creates_filter
domains: [concepts, indicators]
sources: ["N039-double-crossover-method-10-and-50-day-combination-for-stocks", "N039-double-crossover-method-10-and-50-day-combination-for-stocks", "N037-triple-crossover-method-4-9-18-day-moving-average"]
seed_id: commodity_inflation_stock
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# Intermarket filter for moving average crossovers

## Discovery Summary

N039's 10/50 double crossover provides intermediate-term stock signals but is inherently lagging. Murphy's intermarket chain (commodities → bonds → stocks) offers a leading indication of stock direction, which can filter crossover signals to reduce whipsaw. A buy signal is more reliable when the intermarket chain points to rising stocks, while a sell signal is more reliable when it points to falling stocks. N037's faster 4/9/18 triple crossover could use the same intermarket filter for shorter-term confirmation.

## Trading Implication

Before acting on a 10/50 or 4/9/18 crossover signal, check the direction of commodities and bonds and only trade in the direction implied by the intermarket chain; otherwise stand aside or reduce position size.

## Supporting Notes

- [[N039-double-crossover-method-10-and-50-day-combination-for-stocks]]
- [[N039-double-crossover-method-10-and-50-day-combination-for-stocks]]
- [[N037-triple-crossover-method-4-9-18-day-moving-average]]

## Connection Type

**creates_filter** — Actionability score: 4/5
