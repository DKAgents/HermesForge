---
type: insight
date: 2026-10-28
actionability: 4
connection_type: creates_filter
domains: [rules]
sources: ["R142-weekly-signals-as-trend-filters-for-macd-and-stochastics", "R142-weekly-signals-as-trend-filters-for-macd-and-stochastics", "R304-moving-averages-applied-to-long-term-charts"]
seed_id: trend_filter_entry
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# Weekly trend as daily entry filter for MACD/Stochastics

## Discovery Summary

'R142-weekly-signals-as-trend-filters-for-macd-and-stochastics' explicitly states that weekly MACD and Stochastics signals should be used as trend filters before acting on daily crossovers, citing John J. Murphy. 'R304-moving-averages-applied-to-long-term-charts' reinforces the multi-timeframe filtering principle but from the perspective of moving averages on long-term charts. Together they confirm a consistent rule: any daily entry signal must be aligned with the weekly indicator direction to avoid counter-trend trades.

## Trading Implication

A trader should only take daily MACD or Stochastics crossover signals that are in the same direction as the weekly MACD or Stochastics signal (bullish weekly = buy only daily bullish crossovers; bearish weekly = sell only daily bearish crossovers).

## Supporting Notes

- [[R142-weekly-signals-as-trend-filters-for-macd-and-stochastics]]
- [[R142-weekly-signals-as-trend-filters-for-macd-and-stochastics]]
- [[R304-moving-averages-applied-to-long-term-charts]]

## Connection Type

**creates_filter** — Actionability score: 4/5
