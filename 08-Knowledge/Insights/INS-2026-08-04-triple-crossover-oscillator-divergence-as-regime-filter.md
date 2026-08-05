---
type: insight
date: 2026-08-04
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

C128 establishes that MA differences can be treated as oscillators to detect convergence/divergence. R323 and N037 together define the triple crossover method (specifically 4-9-18 day MAs) as a signal system. A non-obvious connection emerges: in ranging or volatile markets, the 4-9-18 triple crossover (N037) generates frequent whipsaw signals, but if the spread between the 4-day and 18-day MAs is viewed as an oscillator per C128, low oscillator amplitude (compressed spread) would signal a ranging regime where triple crossover signals should be filtered out.

## Trading Implication

Before acting on a 4-9-18 triple crossover buy or sell signal, measure the spread between the 4-day and 18-day MAs as an oscillator value; only take signals when the spread is expanding (trending regime), and ignore or reduce size when the spread is compressed or contracting (ranging regime).

## Supporting Notes

- [[C128-moving-averages-as-oscillators-via-double-crossover]]
- [[R323-triple-crossover-method-moving-averages]]
- [[N037-triple-crossover-method-4-9-18-day-moving-average]]

## Connection Type

**creates_filter** — Actionability score: 3/5
