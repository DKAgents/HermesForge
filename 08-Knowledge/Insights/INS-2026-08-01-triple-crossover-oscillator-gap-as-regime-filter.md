---
type: insight
date: 2026-08-01
actionability: 3
connection_type: creates_filter
domains: [concepts, indicators, rules]
sources: ["C128-moving-averages-as-oscillators-via-double-crossover", "R323-triple-crossover-method-moving-averages", "N037-triple-crossover-method-4-9-18-day-moving-average"]
seed_id: pattern_regime
tags: [insight, discovery, knowledge-evolution]
---

# Triple Crossover Oscillator Gap as Regime Filter

## Discovery Summary

C128 establishes that the difference between two moving averages can function as an oscillator reflecting momentum and convergence/divergence. R323 and N037 together define the triple crossover method (4-9-18 day), where all three averages must align for a confirmed signal. In ranging or volatile regimes, the short averages (4-day, 9-day) will whipsaw across the longer 18-day repeatedly without sustained separation — meaning the oscillator spread (per C128 logic) will be narrow and oscillating rather than trending. This oscillator amplitude between the shortest and longest average can serve as a regime detector: low amplitude = ranging/volatile, high amplitude = trending.

## Trading Implication

A trader using the 4-9-18 triple crossover system (N037) should measure the spread between the 4-day and 18-day average as an oscillator (C128); only take crossover signals from R323 when that spread is expanding, not when it is compressed or oscillating near zero, to filter out whipsaw entries in ranging markets.

## Supporting Notes

- [[C128-moving-averages-as-oscillators-via-double-crossover]]
- [[R323-triple-crossover-method-moving-averages]]
- [[N037-triple-crossover-method-4-9-18-day-moving-average]]

## Connection Type

**creates_filter** — Actionability score: 3/5
