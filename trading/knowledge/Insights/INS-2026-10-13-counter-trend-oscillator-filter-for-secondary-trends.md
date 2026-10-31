---
type: insight
date: 2026-10-13
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
# Counter-trend oscillator filter for secondary trends

## Discovery Summary

C366-secondary-trends defines a secondary trend as a corrective move within a larger primary trend. EN041-oscillator-entry-strategy-in-trending-markets entries are predicated on oscillators signaling within the trend direction. If an oscillator gives a counter-trend signal (e.g., overbought in a downtrend) during a secondary trend, it may falsely suggest a reversal when the larger primary trend remains intact, so the rule should require confirmation that the oscillator signal aligns with the primary trend direction, not the secondary.

## Trading Implication

Traders should only take oscillator-based entries when the signal agrees with the primary trend; ignore or fade oscillator signals that align with secondary (counter-trend) moves to avoid premature entries against the dominant direction.

## Supporting Notes

- [[C366-secondary-trends]]
- [[EN041-oscillator-entry-strategy-in-trending-markets]]

## Connection Type

**adds_condition** — Actionability score: 4/5
