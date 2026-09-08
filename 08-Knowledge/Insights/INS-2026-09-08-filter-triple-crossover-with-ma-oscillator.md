---
type: insight
date: 2026-09-08
actionability: 4
connection_type: creates_filter
domains: [concepts, indicators, rules]
sources: ["C128-moving-averages-as-oscillators-via-double-crossover", "R323-triple-crossover-method-moving-averages", "N037-triple-crossover-method-4-9-18-day-moving-average"]
seed_id: pattern_regime
tags: [insight, discovery, knowledge-evolution]
---

# Filter Triple Crossover with MA Oscillator

## Discovery Summary

R323 describes the triple crossover method for generating signals using three moving averages, and N037 details the popular 4-9-18 day implementation. C128 explains that the difference between two moving averages can form an oscillator like MACD, used to gauge momentum and trend. Combining these, the double moving average oscillator can act as a regime filter for triple crossover signals, reducing whipsaws in non-trending environments by requiring the oscillator to confirm directional agreement.

## Trading Implication

Construct an oscillator from the shortest and longest moving averages (e.g., 4- and 18-day) and only take triple crossover signals in the direction of the oscillator's position relative to its zero line to avoid ranging-market failures.

## Supporting Notes

- [[C128-moving-averages-as-oscillators-via-double-crossover]]
- [[R323-triple-crossover-method-moving-averages]]
- [[N037-triple-crossover-method-4-9-18-day-moving-average]]

## Connection Type

**creates_filter** — Actionability score: 4/5
