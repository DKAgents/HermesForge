---
type: insight
date: 2026-08-02
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
# McClellan Breadth Confirms Secondary Trend vs. Oscillator Noise

## Discovery Summary

EN041 warns traders to fade oscillator signals with-trend (buy oversold in uptrends), but the edge condition is that oscillators can stay overbought/oversold for extended periods in strong trends, making individual oscillator readings unreliable. C366 defines secondary trends as 3-week to several-month counter-moves within primary trends — precisely the timeframe where oscillators generate false counter-trend signals. N186's McClellan Oscillator measures broad market breadth rather than a single instrument, offering a structural confirmation layer: if the McClellan Oscillator is also showing sustained overbought/oversold breadth, a secondary trend correction may be genuinely underway rather than an oscillator lie, providing the additional condition EN041 lacks.

## Trading Implication

Before fading an oscillator reading in a strong trend, require confirmation from the McClellan Oscillator — only treat an oversold reading as a with-trend entry (per EN041) if broad market breadth has NOT confirmed a secondary-trend correction; if McClellan also signals extremity across the market, reduce position size or stand aside rather than executing the standard oversold-in-uptrend buy.

## Supporting Notes

- [[C366-secondary-trends]]
- [[EN041-oscillator-entry-strategy-in-trending-markets]]
- [[N186-mcclellan-oscillator]]

## Connection Type

**adds_condition** — Actionability score: 4/5
