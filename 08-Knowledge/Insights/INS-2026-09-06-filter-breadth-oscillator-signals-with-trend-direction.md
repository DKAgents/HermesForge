---
type: insight
date: 2026-09-06
actionability: 4
connection_type: creates_filter
domains: [concepts, indicators, rules]
sources: ["C366-secondary-trends", "EN041-oscillator-entry-strategy-in-trending-markets", "N186-mcclellan-oscillator"]
seed_id: oscillator_trending_market
tags: [insight, discovery, knowledge-evolution]
---

# Filter Breadth Oscillator Signals with Trend Direction

## Discovery Summary

Secondary trends (C366) are counter-trend moves that trap traders using oscillators alone, since oscillators like the McClellan Oscillator (N186) can give overbought/oversold signals during those corrections. Rule EN041 directly addresses this edge condition by requiring that oversold signals only be bought in uptrends and overbought signals only be sold in downtrends. Applying EN041 to the McClellan Oscillator filters out counter-trend trades during secondary trends.

## Trading Implication

Use the McClellan Oscillator only in the direction of the established broad-market primary trend: ignore overbought readings in strong uptrends and oversold readings in strong downtrends to avoid entering premature counter-trend positions.

## Supporting Notes

- [[C366-secondary-trends]]
- [[EN041-oscillator-entry-strategy-in-trending-markets]]
- [[N186-mcclellan-oscillator]]

## Connection Type

**creates_filter** — Actionability score: 4/5
