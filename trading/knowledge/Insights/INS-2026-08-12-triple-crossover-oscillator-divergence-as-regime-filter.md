---
type: insight
date: 2026-08-12
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

C128 establishes that MA differences can function as oscillators to detect convergence/divergence, while N037 and R323 describe the 4-9-18 triple crossover system used in futures. In ranging or volatile markets, the triple crossover (R323/N037) generates frequent whipsaw signals as the short averages repeatedly cross the longer ones. By treating the spread between the 4-day and 18-day MAs as an oscillator (per C128's framework), a trader can detect when the spread is oscillating with low amplitude and high frequency — a regime signature indicating choppy, non-trending conditions where the triple crossover method is most likely to fail.

## Trading Implication

When the 4-18 day MA spread oscillates with diminishing amplitude and frequent zero-crossings, suspend triple crossover signals as they are likely whipsaws; only re-engage when the spread expands and sustains directional momentum.

## Supporting Notes

- [[C128-moving-averages-as-oscillators-via-double-crossover]]
- [[R323-triple-crossover-method-moving-averages]]
- [[N037-triple-crossover-method-4-9-18-day-moving-average]]

## Connection Type

**creates_filter** — Actionability score: 3/5
