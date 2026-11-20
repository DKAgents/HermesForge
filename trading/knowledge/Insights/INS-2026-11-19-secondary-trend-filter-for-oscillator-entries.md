---
type: insight
date: 2026-11-19
actionability: 4
connection_type: creates_filter
domains: [concepts, indicators, rules]
sources: ["C366-secondary-trends", "EN041-oscillator-entry-strategy-in-trending-markets", "N186-mcclellan-oscillator"]
seed_id: oscillator_trending_market
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# Secondary Trend Filter for Oscillator Entries

## Discovery Summary

EN041's oscillator rule to buy oversold conditions in an uptrend and sell overbought conditions in a downtrend becomes reliable only when those conditions occur within a C366 secondary trend—the counter-trend correction or rally within the primary trend. N186's McClellan oscillator can identify breadth-based overbought/oversold extremes, but in strong primary trends these extremes can persist, so using secondary trend context filters out false counter-trend signals. This adds a condition that aligns oscillator entries with the primary trend rather than against it.

## Trading Implication

In a primary uptrend, wait for a secondary pullback and an oversold McClellan oscillator before buying; do not short an overbought McClellan reading in a strong uptrend. In a primary downtrend, use overbought readings during secondary rallies as short-entry opportunities.

## Supporting Notes

- [[C366-secondary-trends]]
- [[EN041-oscillator-entry-strategy-in-trending-markets]]
- [[N186-mcclellan-oscillator]]

## Connection Type

**creates_filter** — Actionability score: 4/5

## Related Notes
- [[INS-2026-11-18-filter-oscillator-entries-with-secondary-trend-context|Filter Oscillator Entries with Secondary Trend Context]]
