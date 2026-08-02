---
type: insight
date: 2026-08-02
actionability: 4
connection_type: adds_condition
domains: [concepts, indicators, rules]
sources: ["C149-rsi-vs-stochastics-volatility-comparison", "N165-relative-strength-index-rsi-overboughtoversold-levels", "R177-filtered-candle-patterns-oscillator-alternatives"]
seed_id: reversal_pattern_oscillator
tags: [insight, discovery, knowledge-evolution]
---

# Dual Oscillator Confirmation Threshold for Candle Reversal Filters

## Discovery Summary

R177 establishes that any oscillator can filter candle patterns, requiring the oscillator to be in overbought/oversold territory before a candle reversal is considered valid. C149 adds a non-obvious refinement: because RSI reaches extremes less frequently than Stochastics, requiring BOTH oscillators to simultaneously confirm overbought/oversold territory produces the highest-quality signals. N165 supplies the specific RSI thresholds (above 70 overbought, below 30 oversold) needed to operationalize this dual-confirmation filter on candle patterns.

## Trading Implication

A trader should only act on a candle reversal pattern when both RSI (above 70 or below 30 per N165) AND Stochastics are simultaneously in their extreme zones, treating single-oscillator confirmation as insufficient; this dual-gate filter reduces false reversals without requiring any new indicator.

## Supporting Notes

- [[C149-rsi-vs-stochastics-volatility-comparison]]
- [[N165-relative-strength-index-rsi-overboughtoversold-levels]]
- [[R177-filtered-candle-patterns-oscillator-alternatives]]

## Connection Type

**adds_condition** — Actionability score: 4/5
