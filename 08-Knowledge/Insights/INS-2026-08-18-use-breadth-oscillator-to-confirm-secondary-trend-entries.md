---
type: insight
date: 2026-08-18
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

EN041 instructs buying oversold conditions in uptrends, but oscillators notoriously give false oversold readings during strong trending phases. C366 identifies secondary trends (counter-trend corrections lasting 3 weeks to months) as the specific context where price becomes oversold within a primary trend. N186's McClellan Oscillator measures broad market breadth, not just price momentum — meaning it can confirm whether an oversold reading reflects a genuine secondary-trend correction in broad participation or a single-instrument distortion, filtering out the 'oscillator lies in strong trends' problem.

## Trading Implication

Before executing an EN041 oversold-in-uptrend buy, require the McClellan Oscillator to also show an oversold extreme, confirming the correction is a true broad secondary trend pullback rather than a momentum artifact in a single instrument.

## Supporting Notes

- [[C366-secondary-trends]]
- [[EN041-oscillator-entry-strategy-in-trending-markets]]
- [[N186-mcclellan-oscillator]]

## Connection Type

**adds_condition** — Actionability score: 4/5
