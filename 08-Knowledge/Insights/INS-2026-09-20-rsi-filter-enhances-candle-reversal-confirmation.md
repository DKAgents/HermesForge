---
type: insight
date: 2026-09-20
actionability: 4
connection_type: adds_condition
domains: [indicators, patterns, rules]
sources: ["C149-rsi-vs-stochastics-volatility-comparison", "N165-relative-strength-index-rsi-overboughtoversold-levels", "R177-filtered-candle-patterns-oscillator-alternatives"]
seed_id: reversal_pattern_oscillator
tags: [insight, discovery, knowledge-evolution]
---

# RSI Filter Enhances Candle Reversal Confirmation

## Discovery Summary

R177 states any oscillator can filter candle patterns, requiring it to be in a presignal zone first. N165 defines RSI's overbought/oversold zones as above 70/below 30, and C149 notes RSI is less volatile than stochastics, producing fewer false extremes. Combining these, RSI in overbought/oversold territory serves as a more reliable presignal filter for candle reversals than stochastics, which triggers extremes too often. This yields a specific confirmation rule: only act on reversal patterns when RSI is beyond 70 or below 30, leveraging RSI's relative stability.

## Trading Implication

Before entering a trade based on a bullish/bearish candle reversal, require RSI to be below 30 (long) or above 70 (short) as a filter. This reduces whipsaw signals compared to using stochastics alone.

## Supporting Notes

- [[C149-rsi-vs-stochastics-volatility-comparison]]
- [[N165-relative-strength-index-rsi-overboughtoversold-levels]]
- [[R177-filtered-candle-patterns-oscillator-alternatives]]

## Connection Type

**adds_condition** — Actionability score: 4/5
