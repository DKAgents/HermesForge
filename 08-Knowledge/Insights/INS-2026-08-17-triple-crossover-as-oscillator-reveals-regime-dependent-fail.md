---
type: insight
date: 2026-08-17
actionability: 3
connection_type: adds_condition
domains: [concepts, indicators, rules]
sources: ["C128-moving-averages-as-oscillators-via-double-crossover", "R323-triple-crossover-method-moving-averages", "N037-triple-crossover-method-4-9-18-day-moving-average"]
seed_id: pattern_regime
tags: [insight, discovery, knowledge-evolution]
---

# Triple Crossover as Oscillator Reveals Regime-Dependent Failure Modes

## Discovery Summary

C128 establishes that MA crossover differences can be viewed as oscillators — meaning the spread between MAs encodes momentum information. R323 and N037 (4-9-18 day system) describe triple crossover signal generation, but neither addresses failure conditions. The non-obvious link is that by treating the 4-9 spread and 9-18 spread as oscillator pairs (per C128's framework), a trader can detect ranging/choppy regimes when the oscillator hovers near zero with frequent small crossings — precisely the condition where R323's crossover signals degrade into whipsaws.

## Trading Implication

Before acting on 4-9-18 triple crossover signals (N037), compute the oscillator value (4-day MA minus 18-day MA); if this spread is compressing toward zero with alternating sign changes, treat the market as ranging and suppress crossover entries until the spread expands meaningfully.

## Supporting Notes

- [[C128-moving-averages-as-oscillators-via-double-crossover]]
- [[R323-triple-crossover-method-moving-averages]]
- [[N037-triple-crossover-method-4-9-18-day-moving-average]]

## Connection Type

**adds_condition** — Actionability score: 3/5
