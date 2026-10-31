---
type: insight
date: 2026-10-29
actionability: 4
connection_type: creates_filter
domains: [concepts, indicators, market_regime, rules]
sources: ["C128-moving-averages-as-oscillators-via-double-crossover", "R323-triple-crossover-method-moving-averages", "N037-triple-crossover-method-4-9-18-day-moving-average"]
seed_id: pattern_regime
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# Filter triple crossover with double-crossover oscillator regime

## Discovery Summary

C128's moving-averages-as-oscillators-via-double-crossover reframes the 4/9 and 9/18 crossovers in N037/R323 as oscillators. In volatile or ranging markets, these oscillators hover around zero and the triple crossover method produces whipsaw signals. Treating the two component double crossovers as oscillators lets a trader require them to point in the same direction before taking the R323 triple crossover signal, avoiding range-bound failures.

## Trading Implication

Do not enter on a triple crossover signal unless both the 4/9 and 9/18 oscillator legs are expanding in the same direction; if either is flat or oscillating, stand aside because the market is likely ranging.

## Supporting Notes

- [[C128-moving-averages-as-oscillators-via-double-crossover]]
- [[R323-triple-crossover-method-moving-averages]]
- [[N037-triple-crossover-method-4-9-18-day-moving-average]]

## Connection Type

**creates_filter** — Actionability score: 4/5
