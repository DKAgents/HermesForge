---
type: insight
date: 2026-08-31
actionability: 3
connection_type: creates_filter
domains: [concepts, indicators, rules]
sources: ["C366-secondary-trends", "EN041-oscillator-entry-strategy-in-trending-markets", "N186-mcclellan-oscillator"]
seed_id: oscillator_trending_market
tags: [insight, discovery, knowledge-evolution]
---

# Oscillator false signals during secondary trend pullbacks

## Discovery Summary

The oscillator entry strategy (EN041) instructs buying oversold conditions in uptrends, but C366-secondary-trends warns that intermediate corrections can last weeks to months. During a secondary counter-trend move, an oscillator like the McClellan Oscillator (N186) could flash oversold prematurely, leading to entries that get run over by the continuation of the correction. The trader must distinguish between an oversold primary uptrend dip and the start of a deeper secondary downtrend.

## Trading Implication

Before entering on an oversold oscillator signal in an uptrend, confirm that the pullback has not exceeded typical secondary trend duration (3+ weeks) or depth, otherwise treat the signal as suspect and wait for the primary trend to reassert.

## Supporting Notes

- [[C366-secondary-trends]]
- [[EN041-oscillator-entry-strategy-in-trending-markets]]
- [[N186-mcclellan-oscillator]]

## Connection Type

**creates_filter** — Actionability score: 3/5
