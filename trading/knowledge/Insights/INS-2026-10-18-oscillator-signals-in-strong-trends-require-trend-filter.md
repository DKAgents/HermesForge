---
type: insight
date: 2026-10-18
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
# Oscillator signals in strong trends require trend filter

## Discovery Summary

C366-secondary-trends describes counter-trend moves within a primary trend. EN041-oscillator-entry-strategy-in-trending-markets likely uses oscillators for entries. In strong trends, oscillators often reach extreme levels but are not reversal signals. This adds a condition: oscillators should only be traded in the direction of the primary trend, ignoring counter-trend signals. Risk rules about counter-trend trades must account for this to avoid false entries.

## Trading Implication

When a strong primary trend is identified, only take oscillator entries that align with that trend, and avoid counter-trend oscillator signals even if they appear overbought/oversold.

## Supporting Notes

- [[C366-secondary-trends]]
- [[EN041-oscillator-entry-strategy-in-trending-markets]]

## Connection Type

**adds_condition** — Actionability score: 4/5
