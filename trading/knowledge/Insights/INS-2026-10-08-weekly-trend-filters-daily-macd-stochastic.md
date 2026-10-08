---
type: insight
date: 2026-10-08
actionability: 4
connection_type: creates_filter
domains: [rules]
sources: ["R142-weekly-signals-as-trend-filters-for-macd-and-stochastics", "R142-weekly-signals-as-trend-filters-for-macd-and-stochastics", "R304-moving-averages-applied-to-long-term-charts"]
seed_id: trend_filter_entry
tags: [insight, discovery, knowledge-evolution]
---

# Weekly trend filters daily MACD/Stochastic

## Discovery Summary

R142-weekly-signals-as-trend-filters-for-macd-and-stochastics specifies that weekly MACD and Stochastics signals should be evaluated first to determine the prevailing trend, and only then act on daily crossovers. R304-moving-averages-applied-to-long-term-charts refers to using longer-term chart trends to filter entries. Together, they create a clear multi-timeframe filter: daily MACD/Stochastic buy signals are only valid when the weekly MACD/Stochastic is in a bullish alignment (e.g., above zero or rising). This prevents counter-trend entries and improves trade reliability.

## Trading Implication

Before entering a daily MACD or Stochastics crossover, check the weekly chart of the same indicator; only take the signal if it aligns with the weekly direction (e.g., weekly MACD above zero for longs).

## Supporting Notes

- [[R142-weekly-signals-as-trend-filters-for-macd-and-stochastics]]
- [[R142-weekly-signals-as-trend-filters-for-macd-and-stochastics]]
- [[R304-moving-averages-applied-to-long-term-charts]]

## Connection Type

**creates_filter** — Actionability score: 4/5
