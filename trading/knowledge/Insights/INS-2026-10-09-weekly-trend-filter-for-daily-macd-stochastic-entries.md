---
type: insight
date: 2026-10-09
actionability: 4
connection_type: creates_filter
domains: [rules]
sources: ["R142-weekly-signals-as-trend-filters-for-macd-and-stochastics", "R142-weekly-signals-as-trend-filters-for-macd-and-stochastics", "R304-moving-averages-applied-to-long-term-charts"]
seed_id: trend_filter_entry
tags: [insight, discovery, knowledge-evolution]
---

# Weekly trend filter for daily MACD/Stochastic entries

## Discovery Summary

R142-weekly-signals-as-trend-filters-for-macd-and-stochastics explicitly states that weekly MACD and Stochastics signals should be evaluated first to determine the prevailing trend before acting on daily crossovers. This creates a clear multi-timeframe filter: only take daily entries in the direction of the weekly indicator signal.

## Trading Implication

Before executing any daily MACD or Stochastic crossover, check the weekly chart for the same indicator's direction and only enter trades aligned with that weekly signal.

## Supporting Notes

- [[R142-weekly-signals-as-trend-filters-for-macd-and-stochastics]]
- [[R142-weekly-signals-as-trend-filters-for-macd-and-stochastics]]
- [[R304-moving-averages-applied-to-long-term-charts]]

## Connection Type

**creates_filter** — Actionability score: 4/5
