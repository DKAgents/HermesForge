---
type: insight
date: 2026-08-14
actionability: 4
connection_type: adds_condition
domains: [concepts, indicators, rules]
sources: ["C366-secondary-trends", "EN041-oscillator-entry-strategy-in-trending-markets", "N186-mcclellan-oscillator"]
seed_id: oscillator_trending_market
tags: [insight, discovery, knowledge-evolution]
---

# Use Breadth Oscillator to Validate Counter-Trend Entries in Primary Trends

## Discovery Summary

EN041 prescribes buying oversold conditions within uptrends, but oscillators notoriously give false signals in strong trends — price can remain overbought/oversold for extended periods. The McClellan Oscillator (N186) measures broad market breadth rather than a single instrument, making it less prone to single-security trend distortion. Secondary trends (C366) represent the precise counter-trend corrections where EN041's oscillator strategy is meant to be applied. By requiring the McClellan Oscillator to confirm oversold breadth conditions before acting on individual instrument oscillator signals during a secondary correction within a primary uptrend, a trader adds a market-wide confirmation layer that reduces false entries during strong trending phases.

## Trading Implication

When an individual instrument's momentum oscillator signals oversold during an uptrend's secondary correction, only take the long entry if the McClellan Oscillator also confirms broad market oversold conditions — this filters out instrument-level oscillator lies that occur when the primary trend is strongly bullish.

## Supporting Notes

- [[C366-secondary-trends]]
- [[EN041-oscillator-entry-strategy-in-trending-markets]]
- [[N186-mcclellan-oscillator]]

## Connection Type

**adds_condition** — Actionability score: 4/5
