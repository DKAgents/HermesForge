---
type: insight
date: 2026-11-10
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
# Filter Oscillator Entries by Secondary Trend Duration

## Discovery Summary

EN041's rule to buy oversold in an uptrend fails when oscillators stay oversold in strong trends; C366 supplies the missing filter by defining secondary corrections as 3-week-to-several-month counter-trend moves. Applying the McClellan Oscillator's overbought/oversold readings only after a pullback has matured into a secondary trend avoids premature entries. This honors the implicit risk rule that counter-trend deviations from the primary trend are where entries should be timed.

## Trading Implication

In a strong uptrend, treat a McClellan oversold reading as an alert, not a buy, until the pullback has lasted at least three weeks; mirror this for shorts in downtrends by waiting for a secondary rally before selling overbought readings.

## Supporting Notes

- [[C366-secondary-trends]]
- [[EN041-oscillator-entry-strategy-in-trending-markets]]
- [[N186-mcclellan-oscillator]]

## Connection Type

**adds_condition** — Actionability score: 4/5
