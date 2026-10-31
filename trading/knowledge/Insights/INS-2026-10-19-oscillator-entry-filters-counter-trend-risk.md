---
type: insight
date: 2026-10-19
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
# Oscillator entry filters counter-trend risk

## Discovery Summary

C366-secondary-trends defines the medium-term trend direction, while EN041-oscillator-entry-strategy-in-trending-markets uses oscillator signals for entries only in the direction of the strong trend. Combining them adds a condition: a trader must first confirm the secondary trend aligns with the oscillator signal before entering, thus avoiding counter-trend trades that risk rules typically penalize.

## Trading Implication

Before taking an oscillator entry signal, verify that the secondary trend (e.g., 20-60 day moving average slope) points in the same direction as the signal; reject any oscillator entry that goes against this secondary trend.

## Supporting Notes

- [[C366-secondary-trends]]
- [[EN041-oscillator-entry-strategy-in-trending-markets]]

## Connection Type

**adds_condition** — Actionability score: 4/5

## Related Notes
- [[INS-2026-10-08-oscillator-entry-filter-in-secondary-trends|Oscillator entry filter in secondary trends]]
