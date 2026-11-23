---
type: insight
date: 2026-11-22
actionability: 4
connection_type: creates_filter
domains: [concepts, edge-conditions, indicators]
sources: ["N190-keltner-channels", "C050-secondary-trend-retracement-range", "E036-adx-based-indicator-selection"]
seed_id: ma_crossover_adx_regime
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# ADX gates Keltner Channel reliability — avoid range whipsaws

## Discovery Summary

E036-ADX-Based Indicator Selection states that MA-based indicators are preferred only when ADX is rising, and oscillators when ADX is falling. Since N190-Keltner-Channels are constructed from an EMA and ATR, they are MA-based and therefore only reliable in rising-ADX trending conditions. C050-Secondary-Trend-Retracement-Range adds that secondary corrections typically retrace 1/3 to 2/3 of the prior move, giving a quantified zone for pullback entries within the trending regime.

## Trading Implication

Check the ADX slope before acting on Keltner Channel breakouts: take signals only when ADX is rising, and use the 1/3-to-2/3 retracement range to time secondary pullback entries. When ADX is falling, ignore Keltner breakout signals and switch to oscillator-based strategies.

## Supporting Notes

- [[N190-keltner-channels]]
- [[C050-secondary-trend-retracement-range]]
- [[E036-adx-based-indicator-selection]]

## Connection Type

**creates_filter** — Actionability score: 4/5

## Related Notes
- [[INS-2026-09-09-keltner-pullback-entries-within-dow-retracement-adx-filter|Keltner Pullback Entries Within Dow Retracement + ADX Filter]]
