---
type: insight
date: 2026-11-08
actionability: 4
connection_type: creates_filter
domains: [concepts, indicators, rules]
sources: ["C149-rsi-vs-stochastics-volatility-comparison", "N165-relative-strength-index-rsi-overboughtoversold-levels", "R177-filtered-candle-patterns-oscillator-alternatives"]
seed_id: reversal_pattern_oscillator
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# Dual Oscillator Filter for Candle Reversal Confirmation

## Discovery Summary

C149 establishes that RSI and Stochastics together provide the best confirmation when both are simultaneously overbought or oversold. N165 defines RSI overbought (>70) and oversold (<30) levels with divergence warnings. R177 states that any oscillator can filter candle patterns, requiring the oscillator to be in its presignal area before a reversal pattern is valid. Combining these, a trader should require both RSI and Stochastics to be in their presignal zones (overbought/oversold) before accepting a candle reversal pattern, as this dual condition reduces false signals.

## Trading Implication

Before acting on a candle reversal pattern, check that both RSI (above 70 or below 30) and Stochastics are in their extreme zones. Only take the reversal if both oscillators confirm, aligning with the stronger signal described in C149.

## Supporting Notes

- [[C149-rsi-vs-stochastics-volatility-comparison]]
- [[N165-relative-strength-index-rsi-overboughtoversold-levels]]
- [[R177-filtered-candle-patterns-oscillator-alternatives]]

## Connection Type

**creates_filter** — Actionability score: 4/5
