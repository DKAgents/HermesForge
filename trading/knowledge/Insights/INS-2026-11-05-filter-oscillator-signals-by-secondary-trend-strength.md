---
type: insight
date: 2026-11-05
actionability: 4
connection_type: adds_condition
domains: [concepts, indicators, rules]
sources: ["C366-secondary-trends", "EN041-oscillator-entry-strategy-in-trending-markets", "N186-mcclellan-oscillator"]
seed_id: oscillator_trending_market
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# Filter oscillator signals by secondary trend strength

## Discovery Summary

EN041's oscillator entry strategy (buy oversold in uptrend) assumes the primary trend is reliable, but C366 secondary trends are counter-trend moves that can cause oscillators to issue false signals in strong trends. The McClellan oscillator (N186) also measures overbought/oversold conditions, yet in a powerful primary trend it can remain overbought, making counter-trend trades risky. Thus, oscillators must be filtered by trend strength: avoid counter-trend entries during strong secondary trends or use trend-following confirmation.

## Trading Implication

Traders should verify the primary trend is not excessively strong before acting on oversold/overbought oscillator signals, and avoid taking counter-trend trades during vigorous secondary trends.

## Supporting Notes

- [[C366-secondary-trends]]
- [[EN041-oscillator-entry-strategy-in-trending-markets]]
- [[N186-mcclellan-oscillator]]

## Connection Type

**adds_condition** — Actionability score: 4/5

## Related Notes
- [[EN041-oscillator-entry-strategy-in-trending-markets|Oscillator Entry Strategy in Trending Markets]]
