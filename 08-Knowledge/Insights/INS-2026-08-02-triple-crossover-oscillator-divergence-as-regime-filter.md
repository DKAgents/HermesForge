---
type: insight
date: 2026-08-02
actionability: 3
connection_type: creates_filter
domains: [concepts, indicators, rules]
sources: ["C128-moving-averages-as-oscillators-via-double-crossover", "R323-triple-crossover-method-moving-averages", "N037-triple-crossover-method-4-9-18-day-moving-average"]
seed_id: pattern_regime
tags: [insight, discovery, knowledge-evolution]
---

# Triple Crossover Oscillator Divergence as Regime Filter

## Discovery Summary

C128 establishes that moving average differences can function as oscillators to detect momentum shifts, while N037 and R323 describe the 4-9-18 triple crossover system for futures. The non-obvious connection is that the spread between all three MAs in the triple crossover system (4-9, 9-18, and 4-18 differences) can be monitored simultaneously as three oscillators — when these oscillators compress toward zero and fail to diverge after a crossover signal, it indicates a ranging/low-volatility regime where R323 buy/sell signals historically fail more often.

## Trading Implication

A trader using the 4-9-18 system (N037) should measure the differential oscillators between each MA pair; only take triple crossover signals (R323) when at least two of the three differentials are expanding post-crossover, filtering out whipsaw entries in compressed, ranging conditions.

## Supporting Notes

- [[C128-moving-averages-as-oscillators-via-double-crossover]]
- [[R323-triple-crossover-method-moving-averages]]
- [[N037-triple-crossover-method-4-9-18-day-moving-average]]

## Connection Type

**creates_filter** — Actionability score: 3/5
