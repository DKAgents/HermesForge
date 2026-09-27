---
type: insight
date: 2026-08-03
actionability: 4
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
# Three-Layer Weekly Framework Filters Daily MACD/Stochastic Entries

## Discovery Summary

R142 establishes that weekly charts must confirm trend direction before acting on daily MACD or Stochastic crossovers. N044 provides the specific weekly trend measurement tools (10/40-week MAs) that can operationalize this filter, while C130 adds a price channel breakout condition as a confirming trend signal. Together, these three notes create a layered weekly trend confirmation framework: the 40-week MA defines the primary trend, the weekly price channel confirms breakout direction, and only then should daily MACD/Stochastic crossovers be traded in the trend direction.

## Trading Implication

Before acting on any daily MACD or Stochastic crossover signal, verify that price is on the correct side of the 40-week MA and that a weekly price channel breakout aligns with the trade direction; reject counter-trend daily signals regardless of their strength.

## Supporting Notes

- [[R142-weekly-signals-as-trend-filters-for-macd-and-stochastics]]
- [[C130-the-weekly-rule-price-channel-as-trend-following-alternative]]
- [[N044-long-term-moving-averages-on-weekly-charts]]

## Connection Type

**creates_filter** — Actionability score: 4/5
