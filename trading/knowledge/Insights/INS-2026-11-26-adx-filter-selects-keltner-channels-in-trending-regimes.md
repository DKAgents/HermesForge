---
type: insight
date: 2026-11-26
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
# ADX filter selects Keltner Channels in trending regimes

## Discovery Summary

Keltner Channels are built around an EMA, so they belong to the moving-average class that E036 ADX-Based Indicator Selection says should be used when ADX is rising (trending); when ADX is falling (ranging), oscillators are preferred. This creates a regime filter for Keltner-based trend/breakout signals. In a rising-ADX regime, C050 Secondary Trend Retracement Range also applies: corrections commonly retrace one-third to two-thirds of the prior move, defining a favorable zone for entries. Combining these notes gives a non-obvious rule for when Keltner Channels are reliable and how to time entries within a confirmed trend.

## Trading Implication

Only act on Keltner Channel trend/breakout signals while ADX is rising; avoid them when ADX is falling. In confirmed ADX-trending markets, time entries near secondary retracements of roughly one-third to two-thirds of the prior move rather than chasing extended prices.

## Supporting Notes

- [[N190-keltner-channels]]
- [[C050-secondary-trend-retracement-range]]
- [[E036-adx-based-indicator-selection]]

## Connection Type

**creates_filter** — Actionability score: 4/5
