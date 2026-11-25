---
type: insight
date: 2026-11-24
actionability: 3
connection_type: creates_filter
domains: [concepts, indicators, trading rules]
sources: ["C366-secondary-trends", "EN041-oscillator-entry-strategy-in-trending-markets", "N186-mcclellan-oscillator"]
seed_id: oscillator_trending_market
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# Breadth Oscillator Filters Counter-Trend Entries in Secondary Trends

## Discovery Summary

EN041's rule to buy oversold in an uptrend can be misapplied in strong trends because oscillators remain overbought/oversold and do not generate pullback signals. C366 defines the safer counter-trend context: a secondary correction within the primary trend. The McClellan Oscillator (N186) provides a breadth-based overbought/oversold check to confirm that a correction is broad enough to be a genuine secondary trend rather than a shallow pause or a primary reversal. This turns the oscillator entry into a filter: only act on EN041 signals when breadth extremes occur during a secondary trend.

## Trading Implication

In a primary uptrend, buy oversold conditions only when the McClellan Oscillator shows a breadth extreme during a secondary correction; in a primary downtrend, sell short overbought conditions only during a secondary rally. If no secondary trend has produced the oscillator extreme, stand aside instead of forcing a counter-trend trade.

## Supporting Notes

- [[C366-secondary-trends]]
- [[EN041-oscillator-entry-strategy-in-trending-markets]]
- [[N186-mcclellan-oscillator]]

## Connection Type

**creates_filter** — Actionability score: 3/5
