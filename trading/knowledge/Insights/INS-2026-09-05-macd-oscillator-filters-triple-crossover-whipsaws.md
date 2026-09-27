---
type: insight
date: 2026-09-05
actionability: 4
connection_type: creates_filter
domains: [concepts, indicators, rules]
sources: ["C128-moving-averages-as-oscillators-via-double-crossover", "R323-triple-crossover-method-moving-averages", "N037-triple-crossover-method-4-9-18-day-moving-average"]
seed_id: pattern_regime
tags: [insight, discovery, knowledge-evolution]
topic: knowledge
confidence: high
has_quotes: false
source: unknown
---
# MACD Oscillator Filters Triple Crossover Whipsaws

## Discovery Summary

The triple crossover method (R323, using 4-9-18 day MAs per N037) generates frequent false signals in ranging or volatile markets. The concept of 'moving averages as oscillators via double crossover' (C128) describes MACD, which measures the spread between two MAs. Applying MACD as a momentum filter to the triple crossover system can reduce failures by ignoring signals when the oscillator shows weak trend strength, effectively requiring the double-crossover spread to confirm the triple-crossover direction.

## Trading Implication

Only take 4-9-18 triple crossover buy signals when the MACD histogram is above zero, and sell signals when it is below zero, to avoid acting on low-momentum whipsaws in ranging markets.

## Supporting Notes

- [[C128-moving-averages-as-oscillators-via-double-crossover]]
- [[R323-triple-crossover-method-moving-averages]]
- [[N037-triple-crossover-method-4-9-18-day-moving-average]]

## Connection Type

**creates_filter** — Actionability score: 4/5
