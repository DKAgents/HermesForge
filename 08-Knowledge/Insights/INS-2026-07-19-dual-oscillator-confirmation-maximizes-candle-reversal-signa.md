---
type: insight
date: 2026-07-19
actionability: 4
connection_type: adds_condition
domains: [concepts, indicators, rules]
sources: ["C149-rsi-vs-stochastics-volatility-comparison", "N165-relative-strength-index-rsi-overboughtoversold-levels", "R177-filtered-candle-patterns-oscillator-alternatives"]
seed_id: reversal_pattern_oscillator
tags: [insight, discovery, knowledge-evolution]
---

# Dual Oscillator Confirmation Maximizes Candle Reversal Signal Quality

## Discovery Summary

C149 establishes that the best oscillator signals occur when RSI and Stochastics are simultaneously in overbought/oversold territory. R177 states that any oscillator — explicitly including RSI — can filter candle reversal patterns, requiring the oscillator to be in its presignal area before a candle pattern is considered valid. N165 defines RSI overbought/oversold thresholds (>70 / <30). Combining these three notes produces a stricter, higher-confidence entry rule: a candle reversal pattern is only acted upon when BOTH RSI (>70 or <30) AND Stochastics are simultaneously in extreme territory, rather than relying on either oscillator alone.

## Trading Implication

A trader should require dual confirmation — RSI above 70 (or below 30) AND Stochastics in overbought (or oversold) — before treating a candle reversal pattern as a valid trade signal, filtering out the more frequent but lower-quality signals that appear when only one oscillator is at an extreme.

## Supporting Notes

- [[C149-rsi-vs-stochastics-volatility-comparison]]
- [[N165-relative-strength-index-rsi-overboughtoversold-levels]]
- [[R177-filtered-candle-patterns-oscillator-alternatives]]

## Connection Type

**adds_condition** — Actionability score: 4/5
