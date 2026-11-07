---
type: insight
date: 2026-11-06
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
# Filter Oscillator Signals with Secondary Trend Duration

## Discovery Summary

EN041's oscillator entry strategy suggests buying oversold conditions in an uptrend, but in strong primary trends, oscillators like the McClellan can remain oversold for extended periods. C366 defines secondary trends as lasting from 3 weeks to several months, so adding a minimum duration filter (e.g., 3 weeks) to oscillator signals distinguishes genuine secondary corrections from shallow, short-lived pullbacks. This prevents premature counter-trend entries and aligns oscillator timing with the natural rhythm of secondary trends.

## Trading Implication

When the McClellan Oscillator (or similar) signals overbought/oversold in a trending market, wait until the counter-trend move has persisted at least three weeks before entering a trade in the direction of the primary trend.

## Supporting Notes

- [[C366-secondary-trends]]
- [[EN041-oscillator-entry-strategy-in-trending-markets]]
- [[N186-mcclellan-oscillator]]

## Connection Type

**adds_condition** — Actionability score: 4/5
