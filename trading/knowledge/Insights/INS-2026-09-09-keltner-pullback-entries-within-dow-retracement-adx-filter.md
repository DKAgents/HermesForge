---
type: insight
date: 2026-09-09
actionability: 4
connection_type: creates_filter
domains: [concepts, edge-conditions, indicators]
sources: ["N190-keltner-channels", "E036-adx-based-indicator-selection", "C050-secondary-trend-retracement-range"]
seed_id: ma_crossover_adx_regime
tags: [insight, discovery, knowledge-evolution]
topic: knowledge
confidence: high
has_quotes: false
source: unknown
---
# Keltner Pullback Entries Within Dow Retracement + ADX Filter

## Discovery Summary

C050 states that secondary trend corrections typically retrace one-third to two-thirds of the prior move. N190 defines Keltner Channels as volatility envelopes around an EMA, which often contain pullbacks. E036 specifies that moving-average-based indicators are preferred when ADX is rising. Together, these notes suggest a high-probability entry when price pulls back to the lower Keltner band, within the 33–66% retracement zone, while ADX is rising.

## Trading Implication

Only enter trend-continuation trades at Keltner Channel band touches when the pullback remains in the 33–66% retracement range and the ADX line is rising.

## Supporting Notes

- [[N190-keltner-channels]]
- [[E036-adx-based-indicator-selection]]
- [[C050-secondary-trend-retracement-range]]

## Connection Type

**creates_filter** — Actionability score: 4/5
