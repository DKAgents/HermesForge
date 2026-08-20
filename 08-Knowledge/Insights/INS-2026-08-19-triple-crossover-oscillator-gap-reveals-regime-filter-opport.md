---
type: insight
date: 2026-08-19
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
# Triple Crossover Oscillator Gap Reveals Regime Filter Opportunity

## Discovery Summary

C128 establishes that the spread between two moving averages can function as an oscillator measuring trend momentum, while N037 and R323 describe the 4-9-18 triple crossover system generating buy/sell signals. A non-obvious connection emerges: the difference between the shortest (4-day) and longest (18-day) MAs in the triple system can be used as a regime oscillator — when this spread is narrow or oscillating around zero, the market is ranging and triple crossover signals from R323 will generate excessive whipsaws, matching the seed question's concern about volatile/ranging regimes.

## Trading Implication

A trader should compute the 4-minus-18-day MA spread as an oscillator before acting on triple crossover buy/sell signals; only take signals when the spread is expanding (trending regime) and filter out or reduce position size when the spread is contracting or flat (ranging regime).

## Supporting Notes

- [[C128-moving-averages-as-oscillators-via-double-crossover]]
- [[R323-triple-crossover-method-moving-averages]]
- [[N037-triple-crossover-method-4-9-18-day-moving-average]]

## Connection Type

**creates_filter** — Actionability score: 3/5
