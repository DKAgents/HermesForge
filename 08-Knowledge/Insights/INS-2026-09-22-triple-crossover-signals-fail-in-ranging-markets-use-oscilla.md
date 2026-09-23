---
type: insight
date: 2026-09-22
actionability: 3
connection_type: adds_condition
domains: [concepts, indicators, market_regime, rules]
sources: ["C128-moving-averages-as-oscillators-via-double-crossover", "R323-triple-crossover-method-moving-averages", "N037-triple-crossover-method-4-9-18-day-moving-average"]
seed_id: pattern_regime
tags: [insight, discovery, knowledge-evolution]
topic: knowledge
confidence: high
has_quotes: false
source: unknown
---
# Triple Crossover Signals Fail in Ranging Markets; Use Oscillator Filter

## Discovery Summary

The triple crossover method (R323, N037) generates signals on MA crossovers, but as noted in C128, moving average crossovers can be viewed as oscillators—and oscillators are prone to whipsaws in ranging markets. The 4-9-18 day combination (N037) is a specific instance of this, and in a ranging regime, these signals frequently fail. The connection suggests that traders should add a regime filter—e.g., require the longer-term moving average to be flat or price to be trending—before acting on crossover signals, effectively converting the oscillator-based signal into a trend-confirmed one.

## Trading Implication

Before taking a 4-9-18 triple crossover signal, verify the market is not range-bound by checking that the longer-term (e.g., 18-day) moving average is sloped in the signal direction. If the market is choppy or the MA is flat, skip the trade to avoid whipsaw losses.

## Supporting Notes

- [[C128-moving-averages-as-oscillators-via-double-crossover]]
- [[R323-triple-crossover-method-moving-averages]]
- [[N037-triple-crossover-method-4-9-18-day-moving-average]]

## Connection Type

**adds_condition** — Actionability score: 3/5
