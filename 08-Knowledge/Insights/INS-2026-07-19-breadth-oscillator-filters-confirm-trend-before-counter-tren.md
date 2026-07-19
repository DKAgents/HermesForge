---
type: insight
date: 2026-07-19
actionability: 4
connection_type: adds_condition
domains: [concepts, indicators, rules]
sources: ["C366-secondary-trends", "EN041-oscillator-entry-strategy-in-trending-markets", "N186-mcclellan-oscillator"]
seed_id: oscillator_trending_market
tags: [insight, discovery, knowledge-evolution]
---

# Breadth Oscillator Filters Confirm Trend Before Counter-Trend Entry

## Discovery Summary

EN041 warns that oscillators mislead in strong trends — buying oversold signals in a downtrend or selling overbought in an uptrend is a classic trap. C366 defines secondary trends as counter-primary corrections lasting weeks to months, which is exactly the timeframe where this trap is most dangerous. N186's McClellan Oscillator adds a breadth dimension: because it measures advancing vs. declining issues across the broad market rather than a single instrument, an extreme McClellan reading can help confirm whether a secondary-trend pullback is a genuine broad-market correction (making EN041's oscillator entry valid) versus a single-stock move against a still-healthy primary trend (where EN041's rule would be dangerous). Using the McClellan Oscillator as a prerequisite filter — only taking oscillator-based oversold entries when the McClellan also confirms broad market weakness — reduces the risk of trading against a primary trend with a single-instrument oscillator alone.

## Trading Implication

Before acting on an oversold oscillator signal in an uptrend, verify the McClellan Oscillator is also showing broad market weakness consistent with a secondary correction; if breadth remains healthy, skip the entry as the pullback is likely a false oscillator reading within a still-strong primary trend.

## Supporting Notes

- [[C366-secondary-trends]]
- [[EN041-oscillator-entry-strategy-in-trending-markets]]
- [[N186-mcclellan-oscillator]]

## Connection Type

**adds_condition** — Actionability score: 4/5
