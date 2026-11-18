---
type: insight
date: 2026-11-17
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
# Oscillator signals need secondary corrections in strong trends

## Discovery Summary

In strong primary trends, the McClellan Oscillator (N186) can stay overbought/oversold for extended periods, making the oversold buy signal from the Oscillator Entry Strategy in Trending Markets (EN041) unreliable unless timed to a secondary correction. The Secondary Trends concept (C366) provides the necessary timing framework: only enter on oscillator extremes that align with the primary trend and occur during a confirmed correction lasting weeks to months, while avoiding counter-trend signals (e.g., selling overbought in an uptrend) because the strong trend overrides these extremes. This adds a filtering condition to the oscillator rule and reinforces the implicit risk rule against counter-trend trades.

## Trading Implication

In a strong uptrend, do not buy oversold readings immediately; wait for a secondary correction to mature (weeks to months) and then buy on oversold. Never sell overbought in a strong uptrend, as the oscillator will remain overbought and the trend dominates.

## Supporting Notes

- [[C366-secondary-trends]]
- [[EN041-oscillator-entry-strategy-in-trending-markets]]
- [[N186-mcclellan-oscillator]]

## Connection Type

**adds_condition** — Actionability score: 4/5

## Related Notes
- [[EN041-oscillator-entry-strategy-in-trending-markets|Oscillator Entry Strategy in Trending Markets]]
