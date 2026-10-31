---
type: insight
date: 2026-10-17
actionability: 4
connection_type: adds_condition
domains: [concepts, rules]
sources: ["C366-secondary-trends", "EN041-oscillator-entry-strategy-in-trending-markets"]
seed_id: oscillator_trending_market
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# Filter oscillator signals with secondary trends

## Discovery Summary

The oscillator entry strategy in trending markets (EN041) can produce false signals when oscillators lie in strong trends, as mentioned in the seed question. The concept of secondary trends (C366) provides a framework to identify the primary trend strength, allowing traders to add a condition: only take oscillator signals that align with the primary trend, ignoring counter-trend signals during strong moves. This interacts with risk rules by reducing exposure to counter-trend trades that often fail in strong trends.

## Trading Implication

Traders should first confirm the primary trend direction using secondary trend analysis (C366) and then only act on oscillator signals (EN041) that are in the same direction, avoiding counter-trend entries during strong trends.

## Supporting Notes

- [[C366-secondary-trends]]
- [[EN041-oscillator-entry-strategy-in-trending-markets]]

## Connection Type

**adds_condition** — Actionability score: 4/5

## Related Notes
- [[EN041-oscillator-entry-strategy-in-trending-markets|Oscillator Entry Strategy in Trending Markets]]
