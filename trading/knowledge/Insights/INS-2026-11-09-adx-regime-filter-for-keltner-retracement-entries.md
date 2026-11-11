---
type: insight
date: 2026-11-09
actionability: 4
connection_type: creates_filter
domains: [edge-conditions, indicators, market concepts]
sources: ["N190-keltner-channels", "C050-secondary-trend-retracement-range", "E036-adx-based-indicator-selection"]
seed_id: ma_crossover_adx_regime
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# ADX regime filter for Keltner retracement entries

## Discovery Summary

Keltner Channels are a moving-average/ATR trend-following band, so E036's ADX rule says they should be trusted only while ADX is rising; in a falling-ADX range, breakouts from these bands are unreliable and oscillators are preferred. When ADX confirms a trending regime, C050's Secondary Trend Retracement Range (pages 61-80) provides the entry timing: wait for a 1/3-to-2/3 retracement, commonly the 50% level, of the prior move before entering in the direction of the primary trend. The non-obvious link is that ADX is not just an indicator selector but the validity condition for Keltner-channel pullback entries, while the retracement range prevents chasing breakouts.

## Trading Implication

Only take Keltner/MA-based trend signals when ADX is rising, and in that regime enter on 50% retracements of the prior leg rather than on breakouts; when ADX is falling, shift to oscillators and avoid Keltner pullback entries.

## Supporting Notes

- [[N190-keltner-channels]]
- [[C050-secondary-trend-retracement-range]]
- [[E036-adx-based-indicator-selection]]

## Connection Type

**creates_filter** — Actionability score: 4/5

## Related Notes
- [[C050-secondary-trend-retracement-range|Secondary Trend Retracement Range]]
