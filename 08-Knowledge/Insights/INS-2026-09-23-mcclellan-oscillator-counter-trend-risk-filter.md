---
type: insight
date: 2026-09-23
actionability: 3
connection_type: adds_condition
domains: [concepts, indicators, rules]
sources: ["C366-secondary-trends", "EN041-oscillator-entry-strategy-in-trending-markets", "N186-mcclellan-oscillator"]
seed_id: oscillator_trending_market
tags: [insight, discovery, knowledge-evolution]
---

# McClellan Oscillator Counter-Trend Risk Filter

## Discovery Summary

C366-secondary-trends describes counter-trend moves lasting 3 weeks to months, while EN041-oscillator-entry-strategy-in-trending-markets advises buying oversold in uptrends. The McClellan Oscillator (N186) measures market breadth overbought/oversold levels, but in strong primary trends oscillator signals often lie, creating false counter-trend signals. The edge condition is that secondary trend counter-moves within a primary trend produce reliable oscillator extremes, but during strong primary trend breakouts the oscillator may stay overbought/oversold and trigger premature fade trades.

## Trading Implication

Only take McClellan Oscillator oversold/overbought entries when price is in a confirmed secondary correction within a primary trend, confirmed by duration (3+ weeks) or retracement depth; avoid signals during strong impulsive primary trend moves where the oscillator stays stretched.

## Supporting Notes

- [[C366-secondary-trends]]
- [[EN041-oscillator-entry-strategy-in-trending-markets]]
- [[N186-mcclellan-oscillator]]

## Connection Type

**adds_condition** — Actionability score: 3/5
