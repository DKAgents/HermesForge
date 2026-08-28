---
type: insight
date: 2026-07-26
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
# Three-Layer Weekly Trend Gate Before Daily Entry

## Discovery Summary

R142 (Weekly Signals as Trend Filters) establishes that MACD and Stochastics daily crossovers must be directionally aligned with the weekly chart signal before acting. N044 (Long-Term MAs on Weekly Charts) provides the structural trend context — the 10/40-week MA relationship defines whether price is in a primary bull or bear trend. C130 (Weekly Price Channel) adds a third confirmation layer: a weekly channel breakout can serve as the initial trend-direction trigger that qualifies which side of R142's filter to apply. Together, the three notes describe a stacked weekly framework — channel breakout (C130) establishes trend direction, 10/40-week MA (N044) confirms primary trend bias, and only then does R142 allow daily MACD/Stochastics crossovers in that direction to generate entries.

## Trading Implication

Before taking any daily MACD or Stochastics crossover signal, a trader should first confirm: (1) price has broken out in that direction on the weekly price channel (C130), and (2) the 10-week MA is on the correct side of the 40-week MA (N044) — only then act on the daily crossover per R142, in the direction of the weekly trend only.

## Supporting Notes

- [[R142-weekly-signals-as-trend-filters-for-macd-and-stochastics]]
- [[C130-the-weekly-rule-price-channel-as-trend-following-alternative]]
- [[N044-long-term-moving-averages-on-weekly-charts]]

## Connection Type

**creates_filter** — Actionability score: 4/5

## Related
- [[EN041-oscillator-entry-strategy-in-trending-markets]] — See foundational oscillator entry rule that this gate refines.

- [[EN070-tight-trendline-break-during-bounce-as-shorting-signal]] — Use tight trendline breaks for entry timing after weekly gate

- [[EN023-trendline-break-confirmation-of-major-trend-change]] — Use long-term trendline break on weekly chart as ultimate trend filter
