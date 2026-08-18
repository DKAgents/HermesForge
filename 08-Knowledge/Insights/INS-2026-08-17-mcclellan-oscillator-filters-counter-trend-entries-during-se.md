---
type: insight
date: 2026-08-17
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
# McClellan Oscillator Filters Counter-Trend Entries During Secondary Corrections

## Discovery Summary

EN041 warns that oscillators can give misleading overbought/oversold signals in strong trends, yet instructs traders to use those same signals as entries. C366 defines secondary trends as counter-primary corrections lasting weeks to months — precisely the timeframe where oscillator signals are most dangerous. N186's McClellan Oscillator measures broad market breadth rather than a single instrument, making it less prone to the 'oscillator lies in strong trends' problem for individual securities. Using McClellan to confirm the broad market is genuinely oversold/overbought before applying EN041's entry rule adds a breadth-confirmation filter that distinguishes true secondary corrections from continuation moves within a strong trend.

## Trading Implication

Before acting on an oscillator oversold signal in an uptrend (per EN041), confirm the McClellan Oscillator also shows broad market oversold conditions — if breadth remains strong while a single instrument's oscillator reads oversold, treat it as a trend-continuation setup and avoid counter-trend entry.

## Supporting Notes

- [[C366-secondary-trends]]
- [[EN041-oscillator-entry-strategy-in-trending-markets]]
- [[N186-mcclellan-oscillator]]

## Connection Type

**adds_condition** — Actionability score: 4/5
