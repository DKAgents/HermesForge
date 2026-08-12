---
type: insight
date: 2026-08-11
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
# McClellan Breadth Filter Validates Oscillator Signals Against Secondary Trends

## Discovery Summary

EN041 prescribes buying oversold conditions in uptrends, but acknowledges the core risk: oscillators give false oversold readings during strong trending moves. C366 defines secondary trends as counter-primary corrections lasting weeks-to-months — precisely the timeframe when oscillators mislead traders into premature counter-trend entries. N186's McClellan Oscillator, being a breadth-based measure rather than a price-momentum measure, provides an independent confirmation layer: if market breadth (advancing vs declining issues) is not broadly oversold alongside price oscillators, the 'oversold' price signal may simply reflect a secondary trend correction within a continuing primary downtrend rather than a genuine reversal opportunity.

## Trading Implication

Before acting on an oversold oscillator signal in an uptrend, require the McClellan Oscillator to also confirm broad market oversold conditions; if price oscillators show oversold but McClellan breadth remains neutral, classify the move as a secondary trend correction and stand aside rather than buying the dip.

## Supporting Notes

- [[C366-secondary-trends]]
- [[EN041-oscillator-entry-strategy-in-trending-markets]]
- [[N186-mcclellan-oscillator]]

## Connection Type

**adds_condition** — Actionability score: 4/5
