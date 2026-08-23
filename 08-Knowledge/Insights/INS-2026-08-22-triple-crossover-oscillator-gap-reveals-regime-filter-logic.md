---
type: insight
date: 2026-08-22
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

C128 establishes that double-crossover MA differences can be used as oscillators to detect momentum divergence. R323 and N037 extend this to triple crossover (4-9-18 day), where the spread between all three MAs encodes regime information. In ranging or volatile markets, the three MAs collapse toward each other (oscillator near zero) and generate frequent whipsaw crossovers — the very condition where these patterns fail most. The oscillator interpretation of C128 provides a measurable threshold to distinguish trending from ranging regimes before applying the triple crossover signals of N037.

## Trading Implication

Before acting on 4-9-18 triple crossover signals (N037/R323), compute the spread between the 4-day and 18-day MA as an oscillator (per C128); only take signals when this spread exceeds a minimum threshold, filtering out trades when the MAs are compressed and a ranging market is implied.

## Supporting Notes

- [[C128-moving-averages-as-oscillators-via-double-crossover]]
- [[R323-triple-crossover-method-moving-averages]]
- [[N037-triple-crossover-method-4-9-18-day-moving-average]]

## Connection Type

**creates_filter** — Actionability score: 3/5
