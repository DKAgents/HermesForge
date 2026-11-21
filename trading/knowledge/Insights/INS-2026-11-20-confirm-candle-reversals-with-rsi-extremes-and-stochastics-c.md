---
type: insight
date: 2026-11-20
actionability: 4
connection_type: adds_condition
domains: [candle patterns, indicators, oscillator filtering, trading rules]
sources: ["C149-rsi-vs-stochastics-volatility-comparison", "N165-relative-strength-index-rsi-overboughtoversold-levels", "R177-filtered-candle-patterns-oscillator-alternatives"]
seed_id: reversal_pattern_oscillator
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# Confirm Candle Reversals with RSI Extremes and Stochastics Confluence

## Discovery Summary

R177 says any oscillator can filter candle reversal patterns, but only if it is already in its overbought/oversold presignal area. C149 adds that RSI is less volatile and reaches extremes less frequently than stochastics, making RSI extremes more meaningful, and the best confirmation occurs when RSI and stochastics are simultaneously overbought/oversold. N165 defines those extremes as above 70 and below 30 and notes divergence as an additional reversal warning. Together, this creates a specific filter: candle reversal patterns should be confirmed by RSI in extreme territory, with stochastics and divergence as strengthening conditions.

## Trading Implication

Before acting on a bearish or bullish candle reversal pattern, require RSI above 70 or below 30, and prefer setups where stochastics is also overbought/oversold or RSI diverges from price. Skip reversal signals lacking this oscillator confirmation.

## Supporting Notes

- [[C149-rsi-vs-stochastics-volatility-comparison]]
- [[N165-relative-strength-index-rsi-overboughtoversold-levels]]
- [[R177-filtered-candle-patterns-oscillator-alternatives]]

## Connection Type

**adds_condition** — Actionability score: 4/5
