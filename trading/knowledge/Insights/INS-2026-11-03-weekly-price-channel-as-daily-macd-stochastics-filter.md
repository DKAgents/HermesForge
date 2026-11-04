---
type: insight
date: 2026-11-03
actionability: 4
connection_type: creates_filter
domains: [MACD, Stochastics, multi-timeframe analysis, trend filtering, weekly price channel]
sources: ["R142-weekly-signals-as-trend-filters-for-macd-and-stochastics", "C130-the-weekly-rule-price-channel-as-trend-following-alternative"]
seed_id: trend_filter_entry
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# Weekly Price Channel as Daily MACD/Stochastics Filter

## Discovery Summary

R142 establishes Murphy's principle that weekly signals should act as trend filters for daily MACD and Stochastics crossovers. C130's Weekly Rule (price channel) offers a simple and historically successful alternative to moving-average trend-following. Combining them, the weekly price channel can define the prevailing trend direction that filters daily entries. This gives a concrete way to implement Murphy's multi-timeframe rule using a breakout-based trend filter.

## Trading Implication

Determine the weekly price-channel trend first; then take only daily MACD/Stochastics crossover signals that align with that weekly direction. If the weekly channel is bullish, avoid short-side daily crossovers, and vice versa.

## Supporting Notes

- [[R142-weekly-signals-as-trend-filters-for-macd-and-stochastics]]
- [[C130-the-weekly-rule-price-channel-as-trend-following-alternative]]

## Connection Type

**creates_filter** — Actionability score: 4/5
