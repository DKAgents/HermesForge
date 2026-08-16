---
type: insight
date: 2026-08-16
actionability: 4
connection_type: adds_condition
domains: [concepts, edge-conditions, indicators]
sources: ["N190-keltner-channels", "E036-adx-based-indicator-selection", "C050-secondary-trend-retracement-range"]
seed_id: ma_crossover_adx_regime
tags: [insight, discovery, knowledge-evolution]
---

# ADX Regime Selects Keltner vs Oscillator at Retracement Zones

## Discovery Summary

E036-adx-based-indicator-selection establishes that ADX distinguishes trending vs ranging regimes and dictates indicator class selection. N190-keltner-channels are MA-based volatility envelopes, meaning per E036 they are only reliable when ADX is rising. C050-secondary-trend-retracement-range identifies that corrections typically reach 33-67% of the prior move, which are precisely the zones where ADX may be ambiguous or falling as the correction unfolds. The non-obvious insight is that ADX state at the retracement zone determines whether Keltner Channel mean-reversion signals at 50% retracement are trustworthy or whether an oscillator should be used instead.

## Trading Implication

At a 33-67% Fibonacci retracement level, check ADX direction before acting: if ADX is rising, use Keltner Channel band touches for trend-continuation entries; if ADX is falling, switch to oscillators for mean-reversion signals and avoid Keltner Channel signals entirely.

## Supporting Notes

- [[N190-keltner-channels]]
- [[E036-adx-based-indicator-selection]]
- [[C050-secondary-trend-retracement-range]]

## Connection Type

**adds_condition** — Actionability score: 4/5
