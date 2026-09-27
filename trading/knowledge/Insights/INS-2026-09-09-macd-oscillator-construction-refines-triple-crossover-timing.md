---
type: insight
date: 2026-09-09
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
# MACD oscillator construction refines triple crossover timing

## Discovery Summary

The triple crossover method (R323, N037) uses 4-9-18 day moving averages to generate signals when shorter averages cross above longer ones, but these signals often fail in ranging or volatile markets. C128 suggests that viewing moving averages as oscillators via double crossover (like MACD) transforms the raw crossover into a momentum indicator that oscillates around a zero line. By applying the oscillator concept to the 4-9-18 triple system, a trader could measure the spread or rate of change between the averages rather than relying solely on binary cross events, adding a condition that filters out weak signals when the oscillator is near zero or failing to confirm direction.

## Trading Implication

Before acting on a 4-9-18 triple crossover signal, compute an oscillator from the spread between the shortest and longest averages (e.g., 4-day minus 18-day) and require it to be above/below a threshold to confirm momentum, avoiding entries during flat or ranging oscillator readings.

## Supporting Notes

- [[C128-moving-averages-as-oscillators-via-double-crossover]]
- [[R323-triple-crossover-method-moving-averages]]
- [[N037-triple-crossover-method-4-9-18-day-moving-average]]

## Connection Type

**adds_condition** — Actionability score: 3/5
