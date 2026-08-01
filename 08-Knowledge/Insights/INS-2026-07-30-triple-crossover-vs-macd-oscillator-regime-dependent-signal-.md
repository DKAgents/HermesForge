---
type: insight
date: 2026-07-30
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
# Triple Crossover vs MACD Oscillator: Regime-Dependent Signal Quality

## Discovery Summary

C128 establishes that moving average differences can be reframed as oscillators (MACD-style), which inherently measures momentum and convergence/divergence. R323 and N037 describe the 4-9-18 triple crossover as a trend-following signal system. The non-obvious connection is that by computing the difference between the short and long MAs of the 4-9-18 system as an oscillator (per C128), a trader can detect when the system is generating signals in a ranging vs. trending regime — oscillator compression near zero indicates range-bound conditions where triple crossover signals historically fail more often.

## Trading Implication

Before acting on a 4-9-18 triple crossover buy or sell signal, compute the (4-day MA minus 18-day MA) oscillator value; if it is compressed near zero with no directional expansion, treat the crossover signal as low-confidence and reduce position size or skip the trade.

## Supporting Notes

- [[C128-moving-averages-as-oscillators-via-double-crossover]]
- [[R323-triple-crossover-method-moving-averages]]
- [[N037-triple-crossover-method-4-9-18-day-moving-average]]

## Connection Type

**adds_condition** — Actionability score: 3/5
