---
type: insight
date: 2026-10-26
actionability: 3
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
# Oscillator entry in secondary trends adds risk

## Discovery Summary

C366-secondary-trends defines counter-trend movements within a larger trend. EN041-oscillator-entry-strategy-in-trending-markets uses oscillators to enter in the direction of the primary trend, but if the oscillator signal occurs during a secondary trend, the trade is effectively counter-trend to the primary move. Risk rules against counter-trend trades should then trigger a filter or reduced position size.

## Trading Implication

Before taking an oscillator entry signal in a trending market, confirm the current price move is not a counter-trend secondary reaction; if it is, either skip the trade or halve position size to align with counter-trend risk rules.

## Supporting Notes

- [[C366-secondary-trends]]
- [[EN041-oscillator-entry-strategy-in-trending-markets]]

## Connection Type

**adds_condition** — Actionability score: 3/5
