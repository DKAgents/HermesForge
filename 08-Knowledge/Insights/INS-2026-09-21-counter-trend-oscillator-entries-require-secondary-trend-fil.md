---
type: insight
date: 2026-09-21
actionability: 3
connection_type: adds_condition
domains: [concepts, indicators, rules]
sources: ["C366-secondary-trends", "EN041-oscillator-entry-strategy-in-trending-markets", "N186-mcclellan-oscillator"]
seed_id: oscillator_trending_market
tags: [insight, discovery, knowledge-evolution]
---

# Counter-Trend Oscillator Entries Require Secondary Trend Filter

## Discovery Summary

EN041-momentum oscillator (e.g., McClellan Oscillator N186) is oversold in an uptrend; however, C366-secondary-trends warns counter-trend moves can last weeks to months. Therefore, a strict primary-trend-only entry ignores that an oscillator oversold during a deep secondary correction may continue lower. The rule must add a secondary-trend confirmation (e.g., price stabilization or oscillator divergence) before buying.

## Trading Implication

When using EN041, for long entries in an uptrend, wait for a secondary-trend bottom signal (e.g., lower low with bullish divergence on McClellan Oscillator) rather than buying the first oversold reading. For shorts in a downtrend, wait for secondary-rally exhaustion.

## Supporting Notes

- [[C366-secondary-trends]]
- [[EN041-oscillator-entry-strategy-in-trending-markets]]
- [[N186-mcclellan-oscillator]]

## Connection Type

**adds_condition** — Actionability score: 3/5
