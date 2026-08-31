---
type: insight
date: 2026-08-31
actionability: 4
connection_type: creates_filter
domains: [concepts, indicators, rules]
sources: ["C128-moving-averages-as-oscillators-via-double-crossover", "R323-triple-crossover-method-moving-averages", "N037-triple-crossover-method-4-9-18-day-moving-average"]
seed_id: pattern_regime
tags: [insight, discovery, knowledge-evolution]
---

# Convert triple crossover spacing into an oscillator to filter signals

## Discovery Summary

The triple crossover method (R323, N037) uses three moving averages to generate signals, but in volatile or ranging markets these crossovers produce frequent whipsaws. By applying the double crossover oscillator concept (C128) to the spacing between the three averages—for example, measuring the spread between the 4-day and 18-day as an oscillator line and the 9-day as a signal line—traders can quantify the rate of convergence or divergence of the triple setup. This converts a binary crossover signal into a momentum condition, allowing signals to be filtered by whether the averages are genuinely diverging (trending) or merely oscillating in a tight band (ranging volatile chop).

## Trading Implication

Before taking a triple crossover signal, compute the difference between the shortest and longest moving averages and only act when this spread is expanding (increasing absolute value), filtering out signals where the averages are contracting or flat—indicating a regime prone to whipsaw failure.

## Supporting Notes

- [[C128-moving-averages-as-oscillators-via-double-crossover]]
- [[R323-triple-crossover-method-moving-averages]]
- [[N037-triple-crossover-method-4-9-18-day-moving-average]]

## Connection Type

**creates_filter** — Actionability score: 4/5
