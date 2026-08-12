---
type: insight
date: 2026-08-12
actionability: 4
connection_type: adds_condition
domains: [concepts, indicators, rules]
sources: ["C366-secondary-trends", "EN041-oscillator-entry-strategy-in-trending-markets", "N186-mcclellan-oscillator"]
seed_id: oscillator_trending_market
tags: [insight, discovery, knowledge-evolution]
---

# Breadth Oscillator Filters Counter-Trend Entries During Secondary Trends

## Discovery Summary

EN041 establishes that oscillators should be used to enter in the direction of the primary trend (buy oversold in uptrend, sell overbought in downtrend), but oscillators notoriously give false signals in strong trends. C366 identifies secondary trends as counter-primary corrections lasting weeks to months — precisely the environment where an oscillator reading 'oversold' may persist. N186's McClellan Oscillator, as a breadth-based instrument, provides a market-wide confirmation layer: if the McClellan Oscillator itself remains in oversold territory during a primary uptrend correction, it suggests the secondary trend correction is broad-based and the oversold reading is potentially actionable, rather than a false signal in a continuing strong trend.

## Trading Implication

When EN041's oscillator entry rule triggers (oversold in uptrend), require the McClellan Oscillator to also confirm oversold breadth conditions before entry — this filters out premature entries during strong secondary-trend selloffs where single-instrument oscillators remain pinned oversold for extended periods.

## Supporting Notes

- [[C366-secondary-trends]]
- [[EN041-oscillator-entry-strategy-in-trending-markets]]
- [[N186-mcclellan-oscillator]]

## Connection Type

**adds_condition** — Actionability score: 4/5
