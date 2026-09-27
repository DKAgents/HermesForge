---
type: insight
date: 2026-08-28
actionability: 4
connection_type: creates_filter
domains: [concepts, indicators, rules]
sources: ["C366-secondary-trends", "EN041-oscillator-entry-strategy-in-trending-markets", "N186-mcclellan-oscillator"]
seed_id: oscillator_trending_market
tags: [insight, discovery, knowledge-evolution]
topic: knowledge
confidence: high
has_quotes: false
source: unknown
---
# Breadth Oscillator Filters Trend-Pullback Entries

## Discovery Summary

C366-secondary-trends defines secondary trends as counter-trend corrections within the primary trend. EN041-oscillator-entry-strategy-in-trending-markets advises buying oversold conditions in an uptrend and selling overbought conditions in a downtrend. The McClellan Oscillator (N186) is a breadth-based overbought/oversold indicator for the broad market. The non-obvious connection is using the McClellan Oscillator as the oversold/overbought filter for EN041's strategy: only enter long when the primary trend is up and the McClellan Oscillator signals broad-market oversold (a secondary trend pullback), and vice versa for shorts.

## Trading Implication

Use a broad-market breadth oscillator like the McClellan Oscillator to time trend-following entries in index products. Enter long only when the primary trend is bullish and the McClellan Oscillator is oversold; enter short only when the primary trend is bearish and the oscillator is overbought.

## Supporting Notes

- [[C366-secondary-trends]]
- [[EN041-oscillator-entry-strategy-in-trending-markets]]
- [[N186-mcclellan-oscillator]]

## Connection Type

**creates_filter** — Actionability score: 4/5
