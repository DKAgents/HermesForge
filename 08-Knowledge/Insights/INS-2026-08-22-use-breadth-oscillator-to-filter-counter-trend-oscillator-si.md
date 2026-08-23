---
type: insight
date: 2026-08-22
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
# Use Breadth Oscillator to Filter Counter-Trend Oscillator Signals

## Discovery Summary

EN041 prescribes buying oversold conditions in uptrends, but oscillators notoriously give premature signals in strong trends. C366 defines secondary trends (3 weeks to several months) as the counter-trend moves where these oversold conditions typically occur. N186's McClellan Oscillator measures broad market breadth overbought/oversold conditions — critically, it operates at the market-wide level, meaning it can confirm whether a secondary trend pullback is a genuine breadth-supported correction or a continuation of a strong primary trend where oscillator signals will fail. Using McClellan as a prerequisite filter before acting on individual oscillator oversold signals resolves the 'oscillators lie in strong trends' problem.

## Trading Implication

Before acting on an oversold oscillator signal during an uptrend (per EN041), require the McClellan Oscillator to also confirm oversold breadth conditions — if McClellan remains elevated or neutral, the secondary trend correction is shallow and the primary trend is still dominant, making the trade premature; only enter when both individual and breadth oscillators signal oversold simultaneously.

## Supporting Notes

- [[C366-secondary-trends]]
- [[EN041-oscillator-entry-strategy-in-trending-markets]]
- [[N186-mcclellan-oscillator]]

## Connection Type

**adds_condition** — Actionability score: 4/5
