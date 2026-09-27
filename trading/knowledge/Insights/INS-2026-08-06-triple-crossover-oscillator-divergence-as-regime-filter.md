---
type: insight
date: 2026-08-06
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

C128 establishes that MA differences can be expressed as oscillators (MACD-style), while N037 and R323 define the triple crossover method (4-9-18 day MAs) as a signal system. A non-obvious connection emerges: the spread between the 4-day and 18-day MAs in the triple crossover system can itself be treated as an oscillator per C128's framework. In ranging or volatile markets, this oscillator will whipsaw repeatedly near zero, producing false crossover signals from R323's buy/sell rules — which directly addresses the seed question about which patterns fail in volatile regimes.

## Trading Implication

Before acting on 4-9-18 triple crossover signals (R323/N037), measure the 4-18 day MA spread as an oscillator; if the spread is oscillating rapidly near zero without sustained directional expansion, treat the regime as ranging and suppress crossover signals until the spread achieves a meaningful threshold distance.

## Supporting Notes

- [[C128-moving-averages-as-oscillators-via-double-crossover]]
- [[R323-triple-crossover-method-moving-averages]]
- [[N037-triple-crossover-method-4-9-18-day-moving-average]]

## Connection Type

**creates_filter** — Actionability score: 3/5
