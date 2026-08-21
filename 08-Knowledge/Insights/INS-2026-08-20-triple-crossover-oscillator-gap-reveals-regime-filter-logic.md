---
type: insight
date: 2026-08-20
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
# Triple Crossover Oscillator Gap Reveals Regime Filter Logic

## Discovery Summary

C128 establishes that MA differences can be viewed as oscillators measuring trend momentum, while R323 and N037 describe the 4-9-18 triple crossover system generating signals via sequential MA alignment. The non-obvious connection is that the spread between all three MAs in the 4-9-18 system (N037) can be interpreted as an oscillator (C128 logic) to detect market regime: when all three MAs are tightly compressed, the oscillator spread collapses, signaling a ranging/low-momentum market where triple crossover signals (R323) historically fail more often.

## Trading Implication

Before acting on a 4-9-18 triple crossover buy or sell signal, measure the spread between the 4-day and 18-day MA as an oscillator value; if the spread is near zero or contracting, treat the signal as low-confidence and reduce position size or skip the trade entirely.

## Supporting Notes

- [[C128-moving-averages-as-oscillators-via-double-crossover]]
- [[R323-triple-crossover-method-moving-averages]]
- [[N037-triple-crossover-method-4-9-18-day-moving-average]]

## Connection Type

**creates_filter** — Actionability score: 3/5
