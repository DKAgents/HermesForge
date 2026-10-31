---
type: insight
date: 2026-10-13
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
# ADX regime filters Keltner Channel strategy choice

## Discovery Summary

E036-adx-based-indicator-selection indicates that indicator choice should depend on ADX trend strength, so Keltner Channels (N190) should be used differently in trending vs. ranging regimes. In high-ADX conditions, Keltner band breaks/trend continuations become more reliable; in low-ADX conditions, fading moves back inside the channel becomes more appropriate. C050-secondary-trend-retracement-range adds the context that the best trend-entry zone is a retracement range, which can be aligned with the Keltner channel bands. This turns three separate concepts into a regime-based trade filter rather than a single always-on signal.

## Trading Implication

Use ADX to select the Keltner Channel mode: trade breakouts/trend pullbacks when ADX is strong, and trade mean-reversion fades at Keltner bands when ADX is weak, while aligning entries with the secondary-trend retracement range.

## Supporting Notes

- [[N190-keltner-channels]]
- [[E036-adx-based-indicator-selection]]
- [[C050-secondary-trend-retracement-range]]

## Connection Type

**creates_filter** — Actionability score: 4/5

## Related Notes
- [[C050-secondary-trend-retracement-range|Secondary Trend Retracement Range]]
