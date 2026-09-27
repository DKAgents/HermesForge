---
type: insight
date: 2026-08-23
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
# Use Breadth Oscillator to Filter Secondary Trend Retracements

## Discovery Summary

EN041 instructs buying oversold conditions in uptrends, but oscillators lie in strong trends — a price oscillator on an individual instrument may stay oversold through an entire secondary correction. The McClellan Oscillator (N186) measures broad market breadth rather than price, making it structurally less prone to this distortion during secondary trends (C366). By requiring the McClellan Oscillator to confirm oversold breadth conditions before acting on individual-instrument oscillator signals during a primary uptrend, a trader gains a market-wide corroboration that the secondary correction is likely exhausted rather than deepening.

## Trading Implication

In a primary uptrend, only execute EN041 oversold buy signals on individual instruments when the McClellan Oscillator simultaneously shows oversold breadth readings, avoiding entries during secondary trend corrections that could persist longer than price oscillators suggest.

## Supporting Notes

- [[C366-secondary-trends]]
- [[EN041-oscillator-entry-strategy-in-trending-markets]]
- [[N186-mcclellan-oscillator]]

## Connection Type

**adds_condition** — Actionability score: 4/5

## Related Notes
- [[C050-secondary-trend-retracement-range|Secondary Trend Retracement Range]]
