---
type: insight
date: 2026-08-21
actionability: 3
connection_type: creates_filter
domains: [concepts, indicators, rules]
sources: ["C128-moving-averages-as-oscillators-via-double-crossover", "R323-triple-crossover-method-moving-averages", "N037-triple-crossover-method-4-9-18-day-moving-average"]
seed_id: pattern_regime
tags: [insight, discovery, knowledge-evolution]
---

# Convert Triple Crossover to Oscillator for Regime Detection

## Discovery Summary

C128 establishes that differences between moving averages can be used as oscillators to detect momentum and divergence. R323 and N037 describe the triple crossover method (4-9-18 day) as a signal generator. The non-obvious connection is that the spread between the 4-day and 18-day MAs from the 4-9-18 system (N037) could be treated as an oscillator per C128's framework, allowing traders to measure oscillator amplitude and detect ranging vs. trending regimes before committing to crossover signals from R323.

## Trading Implication

Before acting on a 4-9-18 triple crossover signal, compute the 4-minus-18 MA spread as an oscillator; if the spread is narrow and oscillating without directional expansion, treat the market as ranging and skip or reduce position size on the crossover signal.

## Supporting Notes

- [[C128-moving-averages-as-oscillators-via-double-crossover]]
- [[R323-triple-crossover-method-moving-averages]]
- [[N037-triple-crossover-method-4-9-18-day-moving-average]]

## Connection Type

**creates_filter** — Actionability score: 3/5
