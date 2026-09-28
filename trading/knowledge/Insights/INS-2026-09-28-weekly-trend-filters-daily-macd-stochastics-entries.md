---
type: insight
date: 2026-09-28
actionability: 4
connection_type: creates_filter
domains: [edge-conditions, indicators, rules]
sources: ["R142-weekly-signals-as-trend-filters-for-macd-and-stochastics", "N044-long-term-moving-averages-on-weekly-charts", "E019-weekly-chart-signals-as-filters-for-short-term-timing"]
seed_id: trend_filter_entry
tags: [insight, discovery, knowledge-evolution]
---

# Weekly trend filters daily MACD/stochastics entries

## Discovery Summary

R142 explicitly uses weekly signals as trend filters for MACD and stochastics, while N044 recommends long-term moving averages on weekly charts to define trend. E019 confirms that weekly chart signals serve as filters for short-term timing. Together, they establish a multi-timeframe rule: daily MACD or stochastic signals are only valid when the weekly trend (e.g., 20-week MA direction or MACD line direction) aligns with the trade direction.

## Trading Implication

Before entering a trade on a daily MACD or stochastic signal, verify that the weekly chart trend (using a long-term moving average or MACD) is in the same direction; take only long signals in weekly uptrends and only short signals in weekly downtrends.

## Supporting Notes

- [[R142-weekly-signals-as-trend-filters-for-macd-and-stochastics]]
- [[N044-long-term-moving-averages-on-weekly-charts]]
- [[E019-weekly-chart-signals-as-filters-for-short-term-timing]]

## Connection Type

**creates_filter** — Actionability score: 4/5
