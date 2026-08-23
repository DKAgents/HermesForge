---
type: insight
date: 2026-08-21
actionability: 4
connection_type: adds_condition
domains: [concepts, indicators, rules]
sources: ["C366-secondary-trends", "EN041-oscillator-entry-strategy-in-trending-markets", "N186-mcclellan-oscillator"]
seed_id: oscillator_trending_market
tags: [insight, discovery, knowledge-evolution]
topic: knowledge
confidence: high
has_quotes: false
source: unknown
---
# Use Breadth Oscillator to Validate Trend Before Counter-Trend Entry

## Discovery Summary

EN041 prescribes buying oversold conditions in uptrends, but oscillators can remain in oversold territory for extended periods during strong trends — a known failure mode. C366 defines secondary trends (counter-primary corrections lasting weeks to months) as the exact context where oversold oscillator readings are most likely to persist and mislead. N186's McClellan Oscillator, being a breadth-based instrument rather than a price-only oscillator, adds a market-wide confirmation layer: if the McClellan Oscillator confirms broad market oversold conditions aligning with the individual security's oscillator signal, the secondary-trend pullback is more likely exhausted and the EN041 entry rule is safer to execute.

## Trading Implication

Before acting on EN041's oversold-in-uptrend buy signal, require the McClellan Oscillator to also show broad market oversold conditions; if breadth is not oversold while price oscillators are, treat the reading as a potential secondary-trend continuation trap and withhold entry.

## Supporting Notes

- [[C366-secondary-trends]]
- [[EN041-oscillator-entry-strategy-in-trending-markets]]
- [[N186-mcclellan-oscillator]]

## Connection Type

**adds_condition** — Actionability score: 4/5
