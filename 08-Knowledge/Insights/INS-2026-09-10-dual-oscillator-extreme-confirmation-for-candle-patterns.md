---
type: insight
date: 2026-09-10
actionability: 4
connection_type: creates_filter
domains: [concepts, indicators, rules]
sources: ["C149-rsi-vs-stochastics-volatility-comparison", "N165-relative-strength-index-rsi-overboughtoversold-levels", "R177-filtered-candle-patterns-oscillator-alternatives"]
seed_id: reversal_pattern_oscillator
tags: [insight, discovery, knowledge-evolution]
---

# Dual Oscillator Extreme Confirmation for Candle Patterns

## Discovery Summary

C149 notes that the best signals occur when both RSI and Stochastics are simultaneously in overbought or oversold territory because RSI reaches extremes less frequently. R177 states any oscillator can filter candle patterns, requiring it to be in its presignal (overbought/oversold) area before a reversal pattern is valid. Together, they suggest that the strongest confirmation for a candle reversal pattern comes when both RSI (e.g., <30 or >70, per N165) and Stochastics %D are simultaneously in extreme territory, not just one oscillator.

## Trading Implication

Only enter trades on reversal candle patterns (e.g., hammers, engulfing) when RSI(14) is above 70 or below 30 AND Stochastics %D is concurrently overbought (>80) or oversold (<20). This dual-filter reduces false signals from milder oscillator readings.

## Supporting Notes

- [[C149-rsi-vs-stochastics-volatility-comparison]]
- [[N165-relative-strength-index-rsi-overboughtoversold-levels]]
- [[R177-filtered-candle-patterns-oscillator-alternatives]]

## Connection Type

**creates_filter** — Actionability score: 4/5
