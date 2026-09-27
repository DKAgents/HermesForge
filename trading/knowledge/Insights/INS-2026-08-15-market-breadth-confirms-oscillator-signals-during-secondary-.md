---
type: insight
date: 2026-08-15
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
# Market Breadth Confirms Oscillator Signals During Secondary Trend Corrections

## Discovery Summary

EN041 instructs buying oversold conditions in uptrends, but oscillators notoriously give false signals in strong trends (the 'oscillators lie' edge case). C366 identifies secondary trends as counter-primary corrections lasting weeks to months — exactly the timeframe where oscillators appear oversold while price keeps falling. N186's McClellan Oscillator adds a breadth dimension: if price is oversold on a momentum oscillator but the McClellan Oscillator confirms broad market deterioration (not just oversold), the secondary trend correction may be deeper than expected, making a counter-trend long entry premature. Conversely, if the McClellan reaches extreme oversold while the primary trend remains bullish, breadth exhaustion confirms EN041's entry trigger with higher confidence.

## Trading Implication

Before executing EN041's oversold-in-uptrend entry, require the McClellan Oscillator to also be at or near an extreme oversold reading to confirm the secondary correction is breadth-driven and nearing exhaustion, not the start of a primary trend reversal; avoid the long entry if McClellan remains neutral or diverges negatively.

## Supporting Notes

- [[C366-secondary-trends]]
- [[EN041-oscillator-entry-strategy-in-trending-markets]]
- [[N186-mcclellan-oscillator]]

## Connection Type

**adds_condition** — Actionability score: 4/5
