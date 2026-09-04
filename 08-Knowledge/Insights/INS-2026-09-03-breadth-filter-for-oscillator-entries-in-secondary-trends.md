---
type: insight
date: 2026-09-03
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
# Breadth Filter for Oscillator Entries in Secondary Trends

## Discovery Summary

Secondary trends (C366) are counter-trend moves that can cause oscillator signals (EN041) to fail because oscillators often remain oversold during corrections within an uptrend. The McClellan Oscillator (N186) measures market breadth and can confirm whether the primary trend is intact. By requiring the McClellan Oscillator to turn up from oversold or cross above zero before acting on an oversold buy signal in an uptrend, traders can filter out false entries during secondary downtrends.

## Trading Implication

Only take oscillator buy signals in an uptrend when the McClellan Oscillator is rising or above zero, confirming broad market strength; this avoids entering on oversold readings that are merely part of an ongoing secondary correction.

## Supporting Notes

- [[C366-secondary-trends]]
- [[EN041-oscillator-entry-strategy-in-trending-markets]]
- [[N186-mcclellan-oscillator]]

## Connection Type

**creates_filter** — Actionability score: 4/5
