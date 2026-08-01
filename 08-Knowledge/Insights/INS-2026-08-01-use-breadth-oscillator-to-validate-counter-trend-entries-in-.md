---
type: insight
date: 2026-08-01
actionability: 4
connection_type: adds_condition
domains: [concepts, indicators, rules]
sources: ["C366-secondary-trends", "EN041-oscillator-entry-strategy-in-trending-markets", "N186-mcclellan-oscillator"]
seed_id: oscillator_trending_market
tags: [insight, discovery, knowledge-evolution]
---

# Use Breadth Oscillator to Validate Counter-Trend Entries in Primary Trends

## Discovery Summary

EN041 establishes that oscillators should be used with trend direction — buy oversold in uptrends, sell overbought in downtrends — but acknowledges the known edge case that oscillators can remain extreme in strong trends. The McClellan Oscillator (N186) provides a breadth-based confirmation layer: because it measures broad market advancing/declining issues rather than a single instrument's price momentum, it is less susceptible to being 'stuck' overbought/oversold from single-stock trend strength. Secondary trends (C366) are the precise timeframe where EN041's counter-trend oscillator entries operate — 3 weeks to several months — meaning McClellan readings at secondary-trend correction lows within a primary uptrend offer a higher-conviction filter than price-based oscillators alone.

## Trading Implication

When a secondary-trend pullback occurs within a primary uptrend and a price-based momentum oscillator shows oversold, require the McClellan Oscillator to also show an oversold reading before entering; this dual confirmation reduces false signals caused by oscillators lying in strongly trending individual instruments.

## Supporting Notes

- [[C366-secondary-trends]]
- [[EN041-oscillator-entry-strategy-in-trending-markets]]
- [[N186-mcclellan-oscillator]]

## Connection Type

**adds_condition** — Actionability score: 4/5
