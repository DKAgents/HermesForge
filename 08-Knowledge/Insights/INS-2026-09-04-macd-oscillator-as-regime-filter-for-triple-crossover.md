---
type: insight
date: 2026-09-04
actionability: 4
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
# MACD oscillator as regime filter for triple crossover

## Discovery Summary

The triple crossover method (R323, N037) generates signals purely from directional alignment of three moving averages, but lacks any measure of trend strength or momentum. C128 introduces viewing moving average differences as oscillators via MACD's double crossover framework. By overlaying MACD's convergence/divergence reading onto the 4-9-18 triple crossover system, a trader can filter out signals generated in weak, ranging, or volatile regimes where the shorter MAs whip—specifically by requiring MACD to confirm directional momentum (e.g., MACD above zero for longs, or histogram expansion) before acting on a triple crossover signal.

## Trading Implication

Before taking a 4-9-18 triple crossover entry, confirm that MACD (constructed from two of the three MAs, such as 4 and 18) is aligned: MACD line above signal/zero for buys, below for sells. Reject triple crossover signals when MACD is flat, contracting, or conflicting with the crossover direction.

## Supporting Notes

- [[C128-moving-averages-as-oscillators-via-double-crossover]]
- [[R323-triple-crossover-method-moving-averages]]
- [[N037-triple-crossover-method-4-9-18-day-moving-average]]

## Connection Type

**adds_condition** — Actionability score: 4/5
