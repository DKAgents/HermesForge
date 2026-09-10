---
type: insight
date: 2026-09-09
actionability: 3
connection_type: creates_filter
domains: [concepts, indicators, rules]
sources: ["R142-weekly-signals-as-trend-filters-for-macd-and-stochastics", "C130-the-weekly-rule-price-channel-as-trend-following-alternative", "N044-long-term-moving-averages-on-weekly-charts"]
seed_id: trend_filter_entry
tags: [insight, discovery, knowledge-evolution]
topic: knowledge
confidence: high
has_quotes: false
source: unknown
---
# Weekly price channel as MACD/Stochastics trend filter

## Discovery Summary

R142 establishes that weekly signals should filter daily MACD and Stochastics entries to prevent counter-trend trading. C130 and N044 offer specific implementations: the weekly price channel (weekly rule) and the 10/40-week moving averages both serve as objective trend-defining tools that can operationalize Murphy's principle by providing a concrete weekly trend reference before accepting daily MACD or Stochastics crossover signals.

## Trading Implication

Before acting on any daily MACD or Stochastics crossover, first confirm whether price is above or below the weekly price channel breakout level or 40-week moving average — only take daily signals in the direction of the weekly trend defined by these tools.

## Supporting Notes

- [[R142-weekly-signals-as-trend-filters-for-macd-and-stochastics]]
- [[C130-the-weekly-rule-price-channel-as-trend-following-alternative]]
- [[N044-long-term-moving-averages-on-weekly-charts]]

## Connection Type

**creates_filter** — Actionability score: 3/5
