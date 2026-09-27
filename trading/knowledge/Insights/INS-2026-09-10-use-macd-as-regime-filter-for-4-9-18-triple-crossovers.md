---
type: insight
date: 2026-09-10
actionability: 3
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
# Use MACD as Regime Filter for 4-9-18 Triple Crossovers

## Discovery Summary

The triple crossover method (R323) generates buy and sell signals when three moving averages align, with the 4-9-18 day combination being widely used (N037). However, moving averages produce false signals in ranging markets. The concept of viewing a double crossover as an oscillator (C128), specifically MACD, provides a way to gauge trend strength. By filtering 4-9-18 crossover signals with MACD’s zero-line or histogram regime check, traders can avoid trades during non-trending conditions.

## Trading Implication

Only take 4-9-18 triple crossover buy signals when MACD is above the zero line (or histogram rising) and sell signals when below, reducing whipsaw losses in volatile or range-bound regimes.

## Supporting Notes

- [[C128-moving-averages-as-oscillators-via-double-crossover]]
- [[R323-triple-crossover-method-moving-averages]]
- [[N037-triple-crossover-method-4-9-18-day-moving-average]]

## Connection Type

**creates_filter** — Actionability score: 3/5
