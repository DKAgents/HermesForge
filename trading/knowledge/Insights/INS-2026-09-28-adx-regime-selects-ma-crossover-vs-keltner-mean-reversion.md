---
type: insight
date: 2026-09-28
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
# ADX regime selects MA crossover vs Keltner mean reversion

## Discovery Summary

E036 ADX-based indicator selection can act as a regime filter: when ADX confirms a trend, MA crossovers become reliable and Keltner Channel entries align with the secondary-trend retracement range in C050. In low-ADX regimes, MA crossovers should be ignored in favor of mean-reversion signals around Keltner Channel extremes. The non-obvious link is that ADX does not just measure trend strength; it tells the trader whether to trust trend-following MA signals or switch to range-based Keltner signals. Secondary retracement entries only make sense when ADX confirms the secondary trend, otherwise the 'retracement' is just range noise.

## Trading Implication

Check ADX first: take MA crossovers and secondary-retracement entries only when ADX is in the trending regime, and fade Keltner Channel extremes when ADX is low. This converts the ADX regime into a hard filter that prevents using trend rules in ranges and range rules in trends.

## Supporting Notes

- [[N190-keltner-channels]]
- [[E036-adx-based-indicator-selection]]
- [[C050-secondary-trend-retracement-range]]

## Connection Type

**creates_filter** — Actionability score: 4/5

## Related Notes
- [[INS-2026-08-28-adx-filters-keltner-channel-entries-by-retracement-depth|ADX filters Keltner Channel entries by retracement depth]]
