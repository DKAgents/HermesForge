---
type: insight
date: 2026-10-19
actionability: 4
connection_type: adds_condition
domains: [concepts, indicators, rules]
sources: ["C128-moving-averages-as-oscillators-via-double-crossover", "R323-triple-crossover-method-moving-averages", "N037-triple-crossover-method-4-9-18-day-moving-average"]
seed_id: pattern_regime
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# Triple crossover failure signals range-bound markets

## Discovery Summary

C128 notes that moving averages can oscillate, failing in ranging markets; R323 and N037 (4-9-18 day triple crossover) confirm this, as whipsaws occur when price oscillates between averages. The triple crossover method lacks an explicit regime filter, so adding an ADX or Bollinger Band squeeze condition can reduce false signals.

## Trading Implication

Before entering a triple crossover signal, check if ADX is below 25 or Bollinger Band width is narrowing; if so, skip the trade or use a tighter stop to avoid whipsaw losses in ranging markets.

## Supporting Notes

- [[C128-moving-averages-as-oscillators-via-double-crossover]]
- [[R323-triple-crossover-method-moving-averages]]
- [[N037-triple-crossover-method-4-9-18-day-moving-average]]

## Connection Type

**adds_condition** — Actionability score: 4/5

## Related Notes
- [[C124-bollinger-band-width-as-volatility-measure|Bollinger Band Width as Volatility Measure]]
