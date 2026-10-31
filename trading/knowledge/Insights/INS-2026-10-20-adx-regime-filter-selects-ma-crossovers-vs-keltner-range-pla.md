---
type: insight
date: 2026-10-20
actionability: 4
connection_type: creates_filter
domains: [concepts, edge-conditions, indicators]
sources: ["N190-keltner-channels", "E036-adx-based-indicator-selection", "C050-secondary-trend-retracement-range"]
seed_id: ma_crossover_adx_regime
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# ADX Regime Filter Selects MA Crossovers vs Keltner Range Plays

## Discovery Summary

E036-adx-based-indicator-selection implies trend-following MA crossovers should only be trusted when ADX confirms a directional regime. In that regime, N190-keltner-channels can define dynamic support/resistance within the pullback zone described by C050-secondary-trend-retracement-range, making Keltner-band touches continuation entries. In low-ADX regimes, the same Keltner bands become mean-reversion boundaries, and MA crossovers lose reliability.

## Trading Implication

Read ADX first: when it confirms a trend, combine MA crossover alignment with Keltner-band touches inside the secondary retracement range for trend entries; when ADX is weak, avoid MA crossovers and instead fade Keltner-band extremes.

## Supporting Notes

- [[N190-keltner-channels]]
- [[E036-adx-based-indicator-selection]]
- [[C050-secondary-trend-retracement-range]]

## Connection Type

**creates_filter** — Actionability score: 4/5
