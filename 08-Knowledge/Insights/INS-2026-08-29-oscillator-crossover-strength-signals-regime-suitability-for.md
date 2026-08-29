---
type: insight
date: 2026-08-29
actionability: 3
connection_type: adds_condition
domains: [concepts, indicators, rules]
sources: ["C128-moving-averages-as-oscillators-via-double-crossover", "R323-triple-crossover-method-moving-averages", "N037-triple-crossover-method-4-9-18-day-moving-average"]
seed_id: pattern_regime
tags: [insight, discovery, knowledge-evolution]
---

# Oscillator crossover strength signals regime suitability for triple MA

## Discovery Summary

C128 notes that the double crossover method gains significance when viewed as an oscillator (like MACD), where the spread between two moving averages indicates momentum strength. R323 and N037 describe the 4-9-18 triple crossover system for generating buy/sell signals. A non-obvious connection is that the MACD-style spread between the 4 and 18 day averages can serve as a pre-filter: when the spread is narrow (oscillator near zero), the market is in a low-momentum, potentially ranging regime where triple crossover signals are prone to whipsaws and should be avoided.

## Trading Implication

Before taking a 4-9-18 triple crossover signal, check if the spread between the 4-day and 18-day moving averages is above a minimum threshold; if the spread is too narrow, skip the trade to reduce whipsaw losses in ranging or volatile markets.

## Supporting Notes

- [[C128-moving-averages-as-oscillators-via-double-crossover]]
- [[R323-triple-crossover-method-moving-averages]]
- [[N037-triple-crossover-method-4-9-18-day-moving-average]]

## Connection Type

**adds_condition** — Actionability score: 3/5
