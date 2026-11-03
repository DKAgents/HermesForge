---
type: insight
date: 2026-11-02
actionability: 4
connection_type: creates_filter
domains: [concepts, indicators, rules]
sources: ["C366-secondary-trends", "EN041-oscillator-entry-strategy-in-trending-markets", "N186-mcclellan-oscillator"]
seed_id: oscillator_trending_market
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# Secondary Trends Filter Oscillator Signals for Primary Trend Entries

## Discovery Summary

Secondary trends (C366-secondary-trends) are the intermediate counter-primary moves that make EN041-oscillator-entry-strategy-in-trending-markets viable: buy oversold readings in uptrends and sell overbought readings in downtrends. In strong trends, oscillators such as N186-mcclellan-oscillator tend to stay overbought/oversold, so acting on raw signals can become a counter-trend trade. The secondary trend context filters out those false signals by requiring the entry to align with the primary trend's direction.

## Trading Implication

Before acting on an overbought/oversold reading from the McClellan Oscillator, label the primary trend; enter only when the oscillator extreme occurs during a secondary move against that primary trend. Do not fade an overbought/oversold reading that is in the same direction as the primary trend.

## Supporting Notes

- [[C366-secondary-trends]]
- [[EN041-oscillator-entry-strategy-in-trending-markets]]
- [[N186-mcclellan-oscillator]]

## Connection Type

**creates_filter** — Actionability score: 4/5
