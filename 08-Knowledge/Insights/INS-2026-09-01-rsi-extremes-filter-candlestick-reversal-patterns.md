---
type: insight
date: 2026-09-01
actionability: 4
connection_type: creates_filter
domains: [concepts, indicators, rules]
sources: ["C149-rsi-vs-stochastics-volatility-comparison", "N165-relative-strength-index-rsi-overboughtoversold-levels", "R177-filtered-candle-patterns-oscillator-alternatives"]
seed_id: reversal_pattern_oscillator
tags: [insight, discovery, knowledge-evolution]
---

# RSI Extremes Filter Candlestick Reversal Patterns

## Discovery Summary

R177 states that any oscillator can filter candle patterns, and N165 defines RSI overbought/oversold as above 70 or below 30. C149 adds that RSI is less volatile than stochastics and reaches extremes less frequently, making its extreme readings a more selective filter; the best signals occur when both RSI and stochastics are simultaneously overbought or oversold. This creates a specific filter: only treat candlestick reversal patterns as valid when RSI is above 70 or below 30, with stronger confirmation if stochastics is also extreme.

## Trading Implication

Before acting on a candlestick reversal pattern, require RSI to be above 70 or below 30; for higher-confidence signals, also require Stochastics to be simultaneously overbought or oversold.

## Supporting Notes

- [[C149-rsi-vs-stochastics-volatility-comparison]]
- [[N165-relative-strength-index-rsi-overboughtoversold-levels]]
- [[R177-filtered-candle-patterns-oscillator-alternatives]]

## Connection Type

**creates_filter** — Actionability score: 4/5
