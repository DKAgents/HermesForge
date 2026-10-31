---
type: insight
date: 2026-10-17
actionability: 4
connection_type: creates_filter
domains: [indicators, intermarket analysis, trading rules]
sources: ["N039-double-crossover-method-10-and-50-day-combination-for-stocks", "N039-double-crossover-method-10-and-50-day-combination-for-stocks", "N037-triple-crossover-method-4-9-18-day-moving-average"]
seed_id: commodity_inflation_stock
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# Intermarket Filter for MA Crossovers

## Discovery Summary

The 10/50 day double crossover (N039) and 4/9/18 triple crossover (N037) generate entry/exit signals. Murphy's intermarket chain (commodities → bonds → stocks) adds a macro confirmation: e.g., a buy signal is more reliable if commodities are falling and bonds are rising, indicating a bullish environment for stocks. This filters out false signals during divergent intermarket conditions.

## Trading Implication

Before acting on a moving average crossover signal, check the intermarket chain: take buy signals only when commodities are down-trending and bonds are up-trending; take sell signals only when commodities are up-trending and bonds are down-trending.

## Supporting Notes

- [[N039-double-crossover-method-10-and-50-day-combination-for-stocks]]
- [[N039-double-crossover-method-10-and-50-day-combination-for-stocks]]
- [[N037-triple-crossover-method-4-9-18-day-moving-average]]

## Connection Type

**creates_filter** — Actionability score: 4/5
