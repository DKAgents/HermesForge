---
type: insight
date: 2026-11-02
actionability: 3
connection_type: creates_filter
domains: [concepts, indicators, rules]
sources: ["C128-moving-averages-as-oscillators-via-double-crossover", "R323-triple-crossover-method-moving-averages", "N037-triple-crossover-method-4-9-18-day-moving-average"]
seed_id: pattern_regime
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# Filter Triple Crossovers with Double-Crossover Oscillator to Avoid Ranging Whipsaws

## Discovery Summary

The triple crossover method (R323; 4-9-18 in N037) is a trend-following signal generator, but repeated crossovers in ranging/volatile markets are false signals. C128 shows that a double crossover can be viewed as an oscillator (MACD-type), measuring the separation between moving averages; this separation is a direct gauge of trend strength/regime. A trader can therefore filter triple-crossover entries by requiring the double-crossover oscillator to be aligned and expanding, reducing whipsaw trades in non-trending markets.

## Trading Implication

Take triple-crossover buy/sell signals only when the double-crossover oscillator confirms the direction with expanding separation; stand aside when the oscillator is flat or crossing zero in a range.

## Supporting Notes

- [[C128-moving-averages-as-oscillators-via-double-crossover]]
- [[R323-triple-crossover-method-moving-averages]]
- [[N037-triple-crossover-method-4-9-18-day-moving-average]]

## Connection Type

**creates_filter** — Actionability score: 3/5
