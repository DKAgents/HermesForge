---
type: insight
date: 2026-08-16
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
# Triple Crossover Oscillator Divergence as Regime Filter

## Discovery Summary

C128 establishes that moving average differences can be viewed as oscillators revealing momentum state, while N037 and R323 describe the 4-9-18 triple crossover system primarily used in futures. The non-obvious connection is that treating the spread between the 4-day and 18-day MAs as an oscillator (per C128's framework) reveals whether the triple crossover signals from R323/N037 are occurring in a trending or ranging regime — rapid oscillator crossings with small amplitude suggest chop, while wide sustained spread confirms trend validity.

## Trading Implication

Before acting on a 4-9-18 triple crossover buy or sell signal, measure the amplitude of the 4-minus-18-day MA difference as an oscillator; if the oscillator is cycling rapidly with low amplitude, treat the crossover as a false signal in a ranging market and skip the trade.

## Supporting Notes

- [[C128-moving-averages-as-oscillators-via-double-crossover]]
- [[R323-triple-crossover-method-moving-averages]]
- [[N037-triple-crossover-method-4-9-18-day-moving-average]]

## Connection Type

**creates_filter** — Actionability score: 3/5
