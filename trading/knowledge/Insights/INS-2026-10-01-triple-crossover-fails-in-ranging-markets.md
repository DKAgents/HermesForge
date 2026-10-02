---
type: insight
date: 2026-10-01
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
# Triple Crossover Fails in Ranging Markets

## Discovery Summary

The concept of moving averages as oscillators (C128) explains why the triple crossover method (R323), as implemented with 4-9-18 day MAs (N037), generates excessive false signals in volatile or ranging markets. The oscillator nature means crossovers occur frequently without real trend changes, so reliability degrades exactly in regimes where the rule is most tempting. This reveals an edge condition: the triple crossover rule should be conditioned on market regime.

## Trading Implication

Assess market regime using a volatility filter (e.g., ATR or Choppiness Index) before acting on a triple crossover. Only take trades when the market shows clear directionality, and ignore crossovers during ranging or high-volatility periods.

## Supporting Notes

- [[C128-moving-averages-as-oscillators-via-double-crossover]]
- [[R323-triple-crossover-method-moving-averages]]
- [[N037-triple-crossover-method-4-9-18-day-moving-average]]

## Connection Type

**adds_condition** — Actionability score: 4/5
