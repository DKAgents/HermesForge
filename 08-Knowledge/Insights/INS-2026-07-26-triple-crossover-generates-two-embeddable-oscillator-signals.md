---
type: insight
date: 2026-07-26
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
# Triple Crossover Generates Two Embeddable Oscillator Signals

## Discovery Summary

C128 establishes that the *difference* between two moving averages is itself an oscillator — the core principle behind MACD. R323 describes a triple crossover system using three MAs of different lengths. Combining these two concepts, the 4-9-18 system from N037 implicitly contains *two* embeddable oscillators: (4−9) and (9−18). Neither R323 nor N037 mentions reading these spreads as oscillators, yet C128's framework makes it actionable — when both spread-oscillators are simultaneously positive (short MA > longer MA on both pairs), the trend confirmation is stronger than a single crossover signal. This connection is non-obvious because N037 treats the 4-9-18 system purely as a crossover rule, never as a dual-oscillator.

## Trading Implication

In the 4-9-18 system, require *both* the (4−9) and (9−18) spread to be positive (or negative) before entering a trade, using them as a dual-oscillator confirmation filter rather than acting on any single MA crossover alone.

## Supporting Notes

- [[C128-moving-averages-as-oscillators-via-double-crossover]]
- [[R323-triple-crossover-method-moving-averages]]
- [[N037-triple-crossover-method-4-9-18-day-moving-average]]

## Connection Type

**creates_filter** — Actionability score: 3/5

## Related
- [[N161-momentum-oscillator-construction]] — See N161-momentum-oscillator-construction for the basic momentum difference principle underlying spread oscillators

- [[EN041-oscillator-entry-strategy-in-trending-markets]] — Apply oscillator entry strategy to these spread-oscillators

- [[N062-macd-divergence-analysis]] — See MACD divergence analysis for interpreting oscillator weakening

- [[C154-macd-histogram-momentum-warning-signals]] — See C154-macd-histogram-momentum-warning-signals for monitoring spread-oscillator momentum before crossovers

## Related Notes
- [[EN041-oscillator-entry-strategy-in-trending-markets|Oscillator Entry Strategy in Trending Markets]]
- [[N062-macd-divergence-analysis|MACD Divergence Analysis]]
