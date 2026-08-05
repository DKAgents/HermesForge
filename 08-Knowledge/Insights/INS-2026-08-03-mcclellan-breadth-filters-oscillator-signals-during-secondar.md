---
type: insight
date: 2026-08-03
actionability: 4
connection_type: creates_filter
domains: [concepts, indicators, rules]
sources: ["C366-secondary-trends", "EN041-oscillator-entry-strategy-in-trending-markets", "N186-mcclellan-oscillator"]
seed_id: oscillator_trending_market
tags: [insight, discovery, knowledge-evolution]
topic: knowledge
confidence: high
has_quotes: false
source: unknown
---
# McClellan Breadth Filters Oscillator Signals During Secondary Trend Corrections

## Discovery Summary

EN041 establishes that oscillators should be used to enter in the direction of the primary trend (buy oversold in uptrends, sell overbought in downtrends), but warns implicitly that oscillators can remain in extreme territory during strong trends. C366 defines secondary trends as counter-primary corrections lasting weeks to months — exactly the conditions where oscillators generate the most misleading signals. N186's McClellan Oscillator measures broad market breadth across advancing/declining issues, providing a market-wide confirmation layer: if the McClellan Oscillator is trending in the direction of the primary trend while price shows a secondary correction, individual oscillator oversold readings become higher-confidence entries rather than potential trend reversals.

## Trading Implication

Before acting on an individual security's oversold oscillator signal during a suspected secondary trend pullback, confirm the McClellan Oscillator is not itself deeply oversold or crossing bearishly — if breadth confirms the primary trend is intact, the individual signal is a valid trend-continuation entry; if breadth is deteriorating, the secondary correction may be becoming a primary reversal and the trade should be skipped.

## Supporting Notes

- [[C366-secondary-trends]]
- [[EN041-oscillator-entry-strategy-in-trending-markets]]
- [[N186-mcclellan-oscillator]]

## Connection Type

**creates_filter** — Actionability score: 4/5
