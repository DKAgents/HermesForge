---
type: insight
date: 2026-07-19
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
# Triple Weekly Confirmation System for Daily Trade Entries

## Discovery Summary

R142 establishes that MACD and Stochastics daily signals must be filtered by weekly trend direction. C130 adds that weekly price channel breakouts (the 'weekly rule') are among the most reliable trend-following methods. N044 specifies that the 10/40-week moving average pair tracks primary trend on weekly charts. Together, these three notes create a layered weekly confirmation framework: a trader can require (1) weekly price channel trend direction from C130, (2) weekly MACD/Stochastics alignment from R142, and (3) price above/below the 40-week MA from N044 before acting on any daily crossover signal — three independent weekly-timeframe confirmations rather than just one.

## Trading Implication

Before entering on a daily MACD or Stochastics crossover, require alignment across all three weekly filters: price must be inside a weekly channel breakout in the intended direction, weekly MACD/Stochastics must confirm the trend, and price must be above (long) or below (short) the 40-week moving average. Entries failing any of these three weekly conditions should be skipped.

## Supporting Notes

- [[R142-weekly-signals-as-trend-filters-for-macd-and-stochastics]]
- [[C130-the-weekly-rule-price-channel-as-trend-following-alternative]]
- [[N044-long-term-moving-averages-on-weekly-charts]]

## Connection Type

**creates_filter** — Actionability score: 4/5

## Related
- [[R141-combining-weekly-and-daily-chart-signals]] — See R141 for the core principle that weekly signals must filter all daily entries

- [[R042-1-3-penetration-criterion-and-two-day-rule-for-neckline-conf]] — See R042-1-3-penetration-criterion-and-two-day-rule-for-neckline-conf|1-3% penetration and two-day rule for daily entry filter after weekly confirmation
