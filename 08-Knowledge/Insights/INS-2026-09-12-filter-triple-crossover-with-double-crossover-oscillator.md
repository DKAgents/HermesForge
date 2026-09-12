---
type: insight
date: 2026-09-12
actionability: 3
connection_type: creates_filter
domains: [concepts, indicators, rules]
sources: ["C128-moving-averages-as-oscillators-via-double-crossover", "R323-triple-crossover-method-moving-averages", "N037-triple-crossover-method-4-9-18-day-moving-average"]
seed_id: pattern_regime
tags: [insight, discovery, knowledge-evolution]
---

# Filter triple crossover with double crossover oscillator

## Discovery Summary

The triple crossover method (R323, N037) generates buy/sell signals on moving average crossovers but is prone to whipsaws in volatile or ranging markets. The double crossover oscillator concept (C128) measures the difference between two moving averages—like a MACD—to gauge momentum and regime. By using the spread between two of the three MAs (e.g., 4-day minus 9-day) as an oscillator, a trader can identify when the market is trendless (oscillator near zero) and filter out triple crossover signals during those choppy periods, only acting when oscillator direction confirms the crossover.

## Trading Implication

Only act on 4-9-18 triple crossover signals when the 4–9 MA spread oscillator is above zero for buys (or below zero for sells) and moving away from the zero line, avoiding signals when the oscillator is flat or crossing near zero.

## Supporting Notes

- [[C128-moving-averages-as-oscillators-via-double-crossover]]
- [[R323-triple-crossover-method-moving-averages]]
- [[N037-triple-crossover-method-4-9-18-day-moving-average]]

## Connection Type

**creates_filter** — Actionability score: 3/5
