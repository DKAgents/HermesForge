---
type: insight
date: 2026-11-14
actionability: 4
connection_type: creates_filter
domains: [market_regime, moving_average_systems, oscillators, trading_rules]
sources: ["C128-moving-averages-as-oscillators-via-double-crossover", "R323-triple-crossover-method-moving-averages", "N037-triple-crossover-method-4-9-18-day-moving-average"]
seed_id: pattern_regime
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# Oscillator-filtered crossovers avoid ranging-market whipsaws

## Discovery Summary

C128 shows that a two-moving-average crossover can be read as an oscillator (MACD), while R323 and N037 use crossover direction for buy/sell signals. In volatile or ranging markets, such crossover signals tend to fail because price crosses the averages repeatedly without a sustained trend. The oscillator interpretation supplies a regime filter: when the double-crossover oscillator stays near zero or fails to expand, the 4-9-18 triple-crossover signals in N037 should not be trusted.

## Trading Implication

Before acting on a triple-crossover signal, check the double-crossover/MACD oscillator for directional expansion. Only trade crossover signals that align with an oscillator move away from zero; in flat or oscillating conditions, stand aside to avoid whipsaw losses.

## Supporting Notes

- [[C128-moving-averages-as-oscillators-via-double-crossover]]
- [[R323-triple-crossover-method-moving-averages]]
- [[N037-triple-crossover-method-4-9-18-day-moving-average]]

## Connection Type

**creates_filter** — Actionability score: 4/5
