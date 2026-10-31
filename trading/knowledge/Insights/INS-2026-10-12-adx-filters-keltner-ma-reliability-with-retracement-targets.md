---
type: insight
date: 2026-10-12
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
# ADX filters Keltner/MA reliability with retracement targets

## Discovery Summary

E036 adx-based-indicator selection implies trend-following signals should only be trusted when ADX confirms the regime. N190 keltner-channels makes this concrete: its middle MA/crossover and breakout signals are reliable in trending ADX conditions, while its bands become mean-reversion levels in low-ADX conditions. C050 secondary-trend-retracement-range supplies the pullback zone where those Keltner/MA continuation or mean-reversion trades should be placed.

## Trading Implication

Use the ADX regime as a filter: in high/rising ADX, trade Keltner MA crossover or breakout signals and look for entries within the C050 secondary-trend pullback range; in low/falling ADX, fade Keltner band touches inside that same range and avoid MA crossovers.

## Supporting Notes

- [[N190-keltner-channels]]
- [[E036-adx-based-indicator-selection]]
- [[C050-secondary-trend-retracement-range]]

## Connection Type

**creates_filter** — Actionability score: 4/5
