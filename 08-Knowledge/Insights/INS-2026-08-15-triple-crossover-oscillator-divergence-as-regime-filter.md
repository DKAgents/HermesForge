---
type: insight
date: 2026-08-15
actionability: 3
connection_type: creates_filter
domains: [concepts, indicators, rules]
sources: ["C128-moving-averages-as-oscillators-via-double-crossover", "R323-triple-crossover-method-moving-averages", "N037-triple-crossover-method-4-9-18-day-moving-average"]
seed_id: pattern_regime
tags: [insight, discovery, knowledge-evolution]
---

# Triple Crossover Oscillator Divergence as Regime Filter

## Discovery Summary

C128 establishes that MA differences can be interpreted as oscillators revealing momentum, while R323 and N037 describe the 4-9-18 triple crossover system. A non-obvious connection is that the spread between all three MAs in the 4-9-18 system can be read as a dual oscillator pair (4-9 spread and 9-18 spread), where compression of both spreads signals a ranging/low-momentum regime where crossover signals fail more frequently. When the 4-9 oscillator and 9-18 oscillator are both near zero simultaneously, the market is likely ranging and triple crossover signals should be filtered out or treated with skepticism.

## Trading Implication

Calculate the 4-9 and 9-18 MA differences as oscillators; only act on triple crossover buy/sell signals when at least one spread shows meaningful separation (non-zero momentum), and avoid trading signals when both spreads are compressed near zero indicating a ranging regime.

## Supporting Notes

- [[C128-moving-averages-as-oscillators-via-double-crossover]]
- [[R323-triple-crossover-method-moving-averages]]
- [[N037-triple-crossover-method-4-9-18-day-moving-average]]

## Connection Type

**creates_filter** — Actionability score: 3/5
