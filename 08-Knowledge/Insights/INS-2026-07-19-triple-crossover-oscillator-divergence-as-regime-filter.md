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

# Triple Crossover Oscillator Divergence as Regime Filter

## Discovery Summary

C128 establishes that the difference between two moving averages can be treated as an oscillator (the MACD principle), while R323 and N037 describe the triple crossover method using three MAs (4-9-18 day). The non-obvious connection is that by computing two separate MA-difference oscillators from the triple crossover system — e.g., (4-day minus 9-day) and (9-day minus 18-day) — a trader can assess whether the two oscillators are converging or diverging. When both oscillators trend together, the market is trending; when they conflict or oscillate around zero, the market is ranging or volatile, which is precisely the regime where triple crossover signals fail most often.

## Trading Implication

Before acting on a 4-9-18 triple crossover buy or sell signal, compute both MA-difference oscillators; only take the signal when both oscillators agree in direction (both positive for longs, both negative for shorts), filtering out whipsaw trades in ranging regimes.

## Supporting Notes

- [[C128-moving-averages-as-oscillators-via-double-crossover]]
- [[R323-triple-crossover-method-moving-averages]]
- [[N037-triple-crossover-method-4-9-18-day-moving-average]]

## Connection Type

**creates_filter** — Actionability score: 3/5
