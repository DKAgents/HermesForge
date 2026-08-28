---
type: insight
date: 2026-08-28
actionability: 4
connection_type: adds_condition
domains: [concepts, edge-conditions, indicators]
sources: ["N190-keltner-channels", "E036-adx-based-indicator-selection", "C050-secondary-trend-retracement-range"]
seed_id: ma_crossover_adx_regime
tags: [insight, discovery, knowledge-evolution]
---

# ADX filters Keltner Channel entries by retracement depth

## Discovery Summary

E036 establishes that rising ADX favors moving-average-based indicators, while N190's Keltner Channels use an exponential MA with ATR bands. C050 adds that secondary trend retracements typically reach 33-67% of the prior move. Combining these: when ADX is rising (trending regime), Keltner Channel breakouts are reliable — but a trader can improve entry timing by only acting on breakouts that occur after price has retraced at least 33% (into the 33-67% retracement zone from C050), aligning the breakout with the completion of the typical secondary correction.

## Trading Implication

During rising ADX environments, wait for price to retrace 33-67% of the prior trend leg before entering on a Keltner Channel breakout — this filters premature entries that occur mid-correction.

## Supporting Notes

- [[N190-keltner-channels]]
- [[E036-adx-based-indicator-selection]]
- [[C050-secondary-trend-retracement-range]]

## Connection Type

**adds_condition** — Actionability score: 4/5
