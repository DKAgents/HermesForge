---
type: insight
date: 2026-08-16
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
# Use Breadth Oscillator to Confirm Secondary Trend Entries

## Discovery Summary

EN041 warns that oscillators 'lie' in strong trends — an oversold reading during a primary uptrend may simply reflect a secondary trend correction (C366), not a genuine reversal, making raw oscillator signals unreliable. The McClellan Oscillator (N186) measures broad market breadth rather than a single instrument, which means it captures whether the secondary trend pullback is narrow (few stocks declining) or broad (systemic selling). Combining EN041's rule — buy oversold in an uptrend — with a McClellan Oscillator filter creates a condition: only act on oversold readings when the McClellan Oscillator confirms the pullback is a shallow secondary correction, not a primary trend change.

## Trading Implication

During a primary uptrend, only take oversold buy signals (EN041) when the McClellan Oscillator is recovering from an oversold extreme, confirming the broad market pullback is a secondary correction (C366) rather than a trend reversal; avoid buying if the McClellan Oscillator is deteriorating toward deeply negative readings.

## Supporting Notes

- [[C366-secondary-trends]]
- [[EN041-oscillator-entry-strategy-in-trending-markets]]
- [[N186-mcclellan-oscillator]]

## Connection Type

**adds_condition** — Actionability score: 4/5
