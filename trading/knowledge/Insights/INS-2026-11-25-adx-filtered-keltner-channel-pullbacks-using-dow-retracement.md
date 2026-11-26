---
type: insight
date: 2026-11-25
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
# ADX-Filtered Keltner Channel Pullbacks Using Dow Retracement Range

## Discovery Summary

E036-ADX-Based Indicator Selection states that rising ADX favors moving-average-based indicators, and Keltner Channels (N190) are MA-based because they wrap an EMA with ATR. C050-Secondary Trend Retracement Range adds that corrections typically retrace one-third to two-thirds, commonly 50%, of the prior move. The non-obvious connection is to use ADX to confirm a trending regime, then use Keltner Channel band touches as timing signals for entries within that retracement zone, especially at the 50% level. This combines regime filtering, volatility envelope support/resistance, and Dow correction norms into a single tactical rule.

## Trading Implication

Trade Keltner Channel pullback signals only when ADX is rising, and place limit entries near the 33%-66% retracement zone (50% preferred) of the prior trend move to improve win rate.

## Supporting Notes

- [[N190-keltner-channels]]
- [[C050-secondary-trend-retracement-range]]
- [[E036-adx-based-indicator-selection]]

## Connection Type

**creates_filter** — Actionability score: 4/5

## Related Notes
- [[INS-2026-10-24-adx-filter-for-keltner-channel-pullback-entries|ADX filter for Keltner channel pullback entries]]
