---
type: insight
date: 2026-09-06
actionability: 4
connection_type: creates_filter
domains: [concepts, indicators, rules]
sources: ["C128-moving-averages-as-oscillators-via-double-crossover", "R323-triple-crossover-method-moving-averages", "N037-triple-crossover-method-4-9-18-day-moving-average"]
seed_id: pattern_regime
tags: [insight, discovery, knowledge-evolution]
---

# Oscillator-Filtered Triple Crossover Signals

## Discovery Summary

C128 describes using the difference between two moving averages as an oscillator. R323 and N037 detail the widely used 4-9-18 day triple crossover method. The oscillator concept can be applied to the 4 and 18 day moving averages to create a momentum filter: only act on triple crossover signals when the 4-18 day difference is clearly positive (for buys) or negative (for sells), avoiding signals when the difference is near zero, which indicates a choppy, trendless market where crossovers frequently fail.

## Trading Implication

Before entering a trade on a 4-9-18 triple crossover, check that the 4-day minus 18-day moving average difference is above a minimum threshold (e.g., 0.5% of price) and expanding; stand aside when the oscillator is near zero.

## Supporting Notes

- [[C128-moving-averages-as-oscillators-via-double-crossover]]
- [[R323-triple-crossover-method-moving-averages]]
- [[N037-triple-crossover-method-4-9-18-day-moving-average]]

## Connection Type

**creates_filter** — Actionability score: 4/5
