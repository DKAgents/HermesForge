---
type: insight
date: 2026-08-13
actionability: 4
connection_type: adds_condition
domains: [concepts, indicators, rules]
sources: ["C366-secondary-trends", "EN041-oscillator-entry-strategy-in-trending-markets", "N186-mcclellan-oscillator"]
seed_id: oscillator_trending_market
tags: [insight, discovery, knowledge-evolution]
---

# Use Breadth Oscillator to Validate Oversold Entries During Secondary Trends

## Discovery Summary

EN041 prescribes buying oversold conditions during uptrends, but oscillators frequently give false oversold readings in strong trends — the classic 'oscillator lie.' C366 defines secondary trends as counter-primary corrections lasting weeks to months, which is precisely when individual oscillators appear oversold. N186's McClellan Oscillator, being a market-breadth measure rather than a price-derived oscillator, offers an independent confirmation layer: if the McClellan Oscillator confirms broad market oversold conditions during a secondary correction in a primary uptrend, the EN041 buy signal has cross-validated breadth support, reducing the risk of buying into a trend reversal rather than a secondary pullback.

## Trading Implication

Only execute EN041 oversold-in-uptrend buy signals when the McClellan Oscillator also registers an oversold reading, confirming the move is a secondary trend correction with broad participation rather than a narrowing trend breakdown.

## Supporting Notes

- [[C366-secondary-trends]]
- [[EN041-oscillator-entry-strategy-in-trending-markets]]
- [[N186-mcclellan-oscillator]]

## Connection Type

**adds_condition** — Actionability score: 4/5
