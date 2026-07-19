---
type: insight
date: 2026-07-19
actionability: 3
connection_type: creates_filter
domains: [concepts, indicators, rules]
sources: ["C128-moving-averages-as-oscillators-via-double-crossover", "R323-triple-crossover-method-moving-averages", "N037-triple-crossover-method-4-9-18-day-moving-average"]
seed_id: pattern_regime
tags: [insight, discovery, knowledge-evolution]
---

# Triple Crossover as Regime Filter via Oscillator Spread

## Discovery Summary

C128 establishes that the difference between two moving averages can function as an oscillator, revealing momentum and convergence/divergence dynamics. R323 and N037 together describe the triple crossover method (4-9-18 day), where three MAs generate signals. The non-obvious connection is that the spread between the shortest (4-day) and longest (18-day) MA in the triple system can be treated as an oscillator per C128's framework — when this spread oscillates tightly around zero without trending, it signals a ranging regime where the triple crossover method itself will generate frequent false whipsaws.

## Trading Implication

Before acting on 4-9-18 triple crossover signals, compute the 4-minus-18 MA spread as an oscillator; if it is mean-reverting and compressed (low absolute value with frequent sign changes), treat the market as ranging and suppress entry signals until the spread shows sustained directional expansion.

## Supporting Notes

- [[C128-moving-averages-as-oscillators-via-double-crossover]]
- [[R323-triple-crossover-method-moving-averages]]
- [[N037-triple-crossover-method-4-9-18-day-moving-average]]

## Connection Type

**creates_filter** — Actionability score: 3/5
