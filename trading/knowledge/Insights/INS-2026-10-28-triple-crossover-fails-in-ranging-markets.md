---
type: insight
date: 2026-10-28
actionability: 3
connection_type: adds_condition
domains: [concepts, indicators, rules]
sources: ["C128-moving-averages-as-oscillators-via-double-crossover", "R323-triple-crossover-method-moving-averages", "N037-triple-crossover-method-4-9-18-day-moving-average"]
seed_id: pattern_regime
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# Triple crossover fails in ranging markets

## Discovery Summary

The triple crossover method (N037, R323) using 4-9-18 day moving averages generates frequent false signals in ranging/volatile markets because oscillating price action repeatedly crosses the moving averages, leading to whipsaws. C128 notes that moving averages act as oscillators via double crossover, and the triple crossover amplifies this effect in non-trending regimes. The seed question identifies an edge condition where these pattern failures are most common.

## Trading Implication

A trader should add a trend filter (e.g., ADX above 25 or price above a 50-day moving average) before taking triple crossover signals, and avoid trading these signals in clearly ranging or high-volatility sideways markets.

## Supporting Notes

- [[C128-moving-averages-as-oscillators-via-double-crossover]]
- [[R323-triple-crossover-method-moving-averages]]
- [[N037-triple-crossover-method-4-9-18-day-moving-average]]

## Connection Type

**adds_condition** — Actionability score: 3/5
