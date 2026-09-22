---
type: insight
date: 2026-09-22
actionability: 4
connection_type: adds_condition
domains: [indicators, patterns, rules]
sources: ["C149-rsi-vs-stochastics-volatility-comparison", "N165-relative-strength-index-rsi-overboughtoversold-levels", "R177-filtered-candle-patterns-oscillator-alternatives"]
seed_id: reversal_pattern_oscillator
tags: [insight, discovery, knowledge-evolution]
---

# RSI Confirms Candle Reversals When Overbought/Oversold

## Discovery Summary

R177 states any oscillator can filter candle patterns if it is in its presignal area, while N165 defines RSI's presignal zones as above 70 or below 30. C149 notes RSI is less volatile than stochastics, meaning its overbought/oversold readings are rarer but more significant. Combining these, an RSI reading beyond 70/30 before a bullish or bearish candle pattern provides a confirmation signal that is less prone to false positives than stochastic-based filters.

## Trading Implication

Before acting on a candle reversal pattern, require RSI to be above 70 (for bearish reversals) or below 30 (for bullish reversals) to confirm the presignal condition. This filters out weak reversal signals and aligns entries with stronger momentum exhaustion.

## Supporting Notes

- [[C149-rsi-vs-stochastics-volatility-comparison]]
- [[N165-relative-strength-index-rsi-overboughtoversold-levels]]
- [[R177-filtered-candle-patterns-oscillator-alternatives]]

## Connection Type

**adds_condition** — Actionability score: 4/5
