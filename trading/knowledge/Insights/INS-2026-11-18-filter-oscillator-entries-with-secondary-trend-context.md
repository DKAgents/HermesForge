---
type: insight
date: 2026-11-18
actionability: 3
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
# Filter Oscillator Entries with Secondary Trend Context

## Discovery Summary

EN041's simple 'buy oversold in uptrend' rule fails in strong trends because oscillators can remain overbought or give shallow dips. C366 defines secondary trends as counter-trend moves lasting weeks to months—these provide the oversold/overbought conditions that oscillators need to generate valid signals. However, since secondary trends are counter to the primary trend, risk rules demand that such entries only be taken in the direction of the primary trend. Thus, the McClellan oscillator (or any oscillator) should be used to time entries during a secondary correction, not as an independent signal.

## Trading Implication

In a strong uptrend, wait for a secondary pullback (confirmed by price structure or trend filters) to reach oversold on the oscillator, then buy; avoid buying on oversold readings that occur outside a secondary trend context, as they may signal a deeper reversal.

## Supporting Notes

- [[C366-secondary-trends]]
- [[EN041-oscillator-entry-strategy-in-trending-markets]]
- [[N186-mcclellan-oscillator]]

## Connection Type

**adds_condition** — Actionability score: 3/5
