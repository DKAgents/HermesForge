---
type: insight
date: 2026-07-31
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
# Triple Crossover Oscillator Gap as Regime Filter

## Discovery Summary

C128 establishes that double-crossover differences can be expressed as oscillators (like MACD), measuring the spread between two MAs as momentum. R323 and N037 extend this to three MAs (specifically 4-9-18 day). The non-obvious connection is that the sequential spread between all three moving averages in the triple crossover system can be used as an oscillator-based regime detector: when the gaps between 4-9 and 9-18 are narrow and oscillating without directional expansion, the market is ranging/volatile rather than trending, which is precisely the condition where triple crossover signals (R323) fail most often.

## Trading Implication

A trader using the 4-9-18 triple crossover system (N037) should calculate the oscillator spread between the short and long MA pairs; when both spreads are compressed and crossing frequently without expansion, suppress trade entries as the market is in a ranging regime where this system historically degrades.

## Supporting Notes

- [[C128-moving-averages-as-oscillators-via-double-crossover]]
- [[R323-triple-crossover-method-moving-averages]]
- [[N037-triple-crossover-method-4-9-18-day-moving-average]]

## Connection Type

**creates_filter** — Actionability score: 3/5

## Related
- [[C152-macd-overbought-and-oversold-conditions]] — See C152-macd-overbought-and-oversold-conditions for applying overbought/oversold thresholds to triple-crossover oscillator gaps

- [[EN041-oscillator-entry-strategy-in-trending-markets]] — Use triple crossover gap as regime filter before applying Murphy's oscillator entry rules

- [[N062-macd-divergence-analysis]] — Use triple MA gap oscillator to filter MACD divergences
