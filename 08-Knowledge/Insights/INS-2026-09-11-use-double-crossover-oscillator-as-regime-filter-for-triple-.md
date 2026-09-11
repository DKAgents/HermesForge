---
type: insight
date: 2026-09-11
actionability: 3
connection_type: creates_filter
domains: [concepts, indicators, rules]
sources: ["C128-moving-averages-as-oscillators-via-double-crossover", "R323-triple-crossover-method-moving-averages", "N037-triple-crossover-method-4-9-18-day-moving-average"]
seed_id: pattern_regime
tags: [insight, discovery, knowledge-evolution]
---

# Use double crossover oscillator as regime filter for triple crossover

## Discovery Summary

C128 notes that the difference between two moving averages can be viewed as an oscillator (e.g., MACD), giving the double crossover method more significance. The triple crossover method (R323) using 4-9-18 day averages (N037) is a trend-following system prone to whipsaws in ranging or volatile markets. By overlaying the oscillator formed from the 4-18 spread, traders can detect when the market is in a non-trending regime where triple crossover signals are more likely to fail.

## Trading Implication

Before acting on a 4-9-18 triple crossover signal, check the spread between the 4-day and 18-day moving averages as an oscillator; only take long signals when the oscillator is clearly positive and short signals when clearly negative, filtering out signals when the oscillator is flat or near zero.

## Supporting Notes

- [[C128-moving-averages-as-oscillators-via-double-crossover]]
- [[R323-triple-crossover-method-moving-averages]]
- [[N037-triple-crossover-method-4-9-18-day-moving-average]]

## Connection Type

**creates_filter** — Actionability score: 3/5
