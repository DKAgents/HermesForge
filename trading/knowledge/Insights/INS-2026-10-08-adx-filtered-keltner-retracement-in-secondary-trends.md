---
type: insight
date: 2026-10-08
actionability: 4
connection_type: creates_filter
domains: [concepts, edge-conditions, indicators]
sources: ["N190-keltner-channels", "E036-adx-based-indicator-selection", "C050-secondary-trend-retracement-range"]
seed_id: ma_crossover_adx_regime
tags: [insight, discovery, knowledge-evolution]
---

# ADX Filtered Keltner Retracement in Secondary Trends

## Discovery Summary

E036-adx-based-indicator-selection uses ADX to distinguish trending from ranging regimes, telling traders when trend-following signals are reliable. N190-keltner-channels provides volatility bands that can frame pullbacks, while C050-secondary-trend-retracement-range identifies where retracements typically end. By applying ADX as a filter, Keltner band touches or breaks become valid continuation signals only in strong trends, and the retracement range confirms the entry zone. This combination transforms a generic Keltner retracement setup into a regime-aware trading rule.

## Trading Implication

In a high-ADX trend, take longs near the Keltner lower band within the secondary retracement range; ignore such retracement setups when ADX is low or declining.

## Supporting Notes

- [[N190-keltner-channels]]
- [[E036-adx-based-indicator-selection]]
- [[C050-secondary-trend-retracement-range]]

## Connection Type

**creates_filter** — Actionability score: 4/5

## Related
- [[C048-dows-three-tier-trend-classification]] — See C048 for definition of secondary trend context
