---
type: insight
date: 2026-08-10
actionability: 3
connection_type: adds_condition
domains: [concepts, indicators, rules]
sources: ["C128-moving-averages-as-oscillators-via-double-crossover", "R323-triple-crossover-method-moving-averages", "N037-triple-crossover-method-4-9-18-day-moving-average"]
seed_id: pattern_regime
tags: [insight, discovery, knowledge-evolution]
topic: knowledge
confidence: high
has_quotes: false
source: unknown
---
# MA Crossover Regime Failure: Oscillator View Reveals Ranging Markets

## Discovery Summary

C128 establishes that the difference between two moving averages can be viewed as an oscillator (MACD-style), which reveals mean-reverting or ranging behavior when the oscillator fluctuates around zero without trending. R323 and N037 describe the triple crossover method (specifically 4-9-18 day periods from N037) as generating buy/sell signals via sequential crossovers. The non-obvious connection is that viewing the 4-9-18 crossover spreads as oscillators (per C128) can diagnose regime: in a ranging market, the shorter MA difference oscillates tightly around zero, generating whipsaws, while in a trending regime it expands directionally.

## Trading Implication

Before acting on a 4-9-18 triple crossover signal, compute the spread between the 4 and 18 day MAs as an oscillator; if it is mean-reverting or compressed near zero, suppress the crossover signal as a likely whipsaw in a ranging regime.

## Supporting Notes

- [[C128-moving-averages-as-oscillators-via-double-crossover]]
- [[R323-triple-crossover-method-moving-averages]]
- [[N037-triple-crossover-method-4-9-18-day-moving-average]]

## Connection Type

**adds_condition** — Actionability score: 3/5
