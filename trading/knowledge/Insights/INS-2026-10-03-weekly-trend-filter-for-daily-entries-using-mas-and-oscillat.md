---
type: insight
date: 2026-10-03
actionability: 4
connection_type: creates_filter
domains: [edge-conditions, indicators, rules]
sources: ["R142-weekly-signals-as-trend-filters-for-macd-and-stochastics", "N044-long-term-moving-averages-on-weekly-charts", "E019-weekly-chart-signals-as-filters-for-short-term-timing"]
seed_id: trend_filter_entry
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# Weekly Trend Filter for Daily Entries Using MAs and Oscillators

## Discovery Summary

R142 weekly-signals-as-trend-filters-for-macd-and-stochastics aligns with N044 long-term-moving-averages-on-weekly-charts to define trend direction, and E019 weekly-chart-signals-as-filters-for-short-term-timing applies that trend as a filter for daily entries. Together they form a multi-timeframe filter consistent with Murphy's advice: use weekly trend (via long-term MA and weekly MACD/stochastics) as a higher-level confirmation before acting on daily signals, thereby improving timing and reducing false entries.

## Trading Implication

Before entering daily trades, confirm weekly trend using long-term moving averages (e.g., 30-week) and weekly MACD/stochastics alignment; only take daily signals in the direction of the weekly trend (e.g., long daily entries when weekly trend is up and weekly oscillators not overbought).

## Supporting Notes

- [[R142-weekly-signals-as-trend-filters-for-macd-and-stochastics]]
- [[N044-long-term-moving-averages-on-weekly-charts]]
- [[E019-weekly-chart-signals-as-filters-for-short-term-timing]]

## Connection Type

**creates_filter** — Actionability score: 4/5
