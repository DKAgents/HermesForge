---
type: insight
date: 2026-10-04
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
# Weekly Trend as Daily Entry Filter

## Discovery Summary

R142, N044, and E019 together establish a multi-timeframe filter: use weekly chart signals (e.g., long-term moving averages from N044, MACD/stochastic from R142) to determine trend direction, then only take daily entries when the weekly trend aligns. This mirrors Murphy's concept of using weekly trend to filter daily entries, adding a condition that short-term timing (E019) should only trigger in the direction of the weekly bias.

## Trading Implication

Before entering a daily trade based on MACD or stochastic signals, confirm the weekly chart shows an aligned trend (e.g., price above its long-term moving average) — otherwise skip the trade.

## Supporting Notes

- [[R142-weekly-signals-as-trend-filters-for-macd-and-stochastics]]
- [[N044-long-term-moving-averages-on-weekly-charts]]
- [[E019-weekly-chart-signals-as-filters-for-short-term-timing]]

## Connection Type

**creates_filter** — Actionability score: 4/5

## Related Notes
- [[E019-weekly-chart-signals-as-filters-for-short-term-timing|Weekly Chart Signals as Filters for Short-Term Timing]]
