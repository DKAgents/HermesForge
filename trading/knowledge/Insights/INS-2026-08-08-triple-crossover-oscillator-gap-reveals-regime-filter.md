---
type: insight
date: 2026-08-08
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
# Triple Crossover Oscillator Gap Reveals Regime Filter

## Discovery Summary

C128 establishes that the difference between two moving averages can function as an oscillator revealing momentum regime. R323 and N037 describe triple crossover systems (specifically the 4-9-18 day combination) that generate signals via sequential MA crossovers. The non-obvious connection is that by treating the spread between the 4-day and 18-day MAs as an oscillator (per C128's framework), a trader can measure whether the market is trending or ranging BEFORE acting on triple crossover signals from R323/N037 — using the oscillator width as a regime pre-filter rather than waiting for crossover failures to occur.

## Trading Implication

Before executing a 4-9-18 triple crossover signal (N037/R323), compute the 4-minus-18 MA spread as an oscillator; if the spread is oscillating tightly around zero (ranging regime), suppress the crossover signal since MA-based patterns fail more frequently in non-trending conditions.

## Supporting Notes

- [[C128-moving-averages-as-oscillators-via-double-crossover]]
- [[R323-triple-crossover-method-moving-averages]]
- [[N037-triple-crossover-method-4-9-18-day-moving-average]]

## Connection Type

**creates_filter** — Actionability score: 3/5
