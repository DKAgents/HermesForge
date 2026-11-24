---
type: insight
date: 2026-11-23
actionability: 4
connection_type: resolves_conflict
domains: [concepts, indicators, trading rules]
sources: ["C366-secondary-trends", "EN041-oscillator-entry-strategy-in-trending-markets", "N186-mcclellan-oscillator"]
seed_id: oscillator_trending_market
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# Oscillator entries are secondary-trend trades, not counter-trend trades

## Discovery Summary

EN041-oscillator-entry-strategy-in-trending-markets says to buy oversold in an uptrend, which appears to be a counter-trend trade. C366-secondary-trends clarifies that this oversold condition occurs during a secondary correction against the primary trend, so the entry is actually with the primary trend. The McClellan Oscillator (N186) can confirm the breadth extreme, while the secondary-trend time frame filters out oscillator readings that lie in strong trends.

## Trading Implication

Treat EN041 signals as valid only after a secondary correction of roughly three weeks to months within a clear primary trend; do not act on short-lived oscillator extremes in strong trends. Use McClellan breadth to confirm the extreme before entering.

## Supporting Notes

- [[C366-secondary-trends]]
- [[EN041-oscillator-entry-strategy-in-trending-markets]]
- [[N186-mcclellan-oscillator]]

## Connection Type

**resolves_conflict** — Actionability score: 4/5
