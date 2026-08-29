---
type: insight
date: 2026-08-29
actionability: 4
connection_type: creates_filter
domains: [concepts, indicators, patterns, rules]
sources: ["C149-rsi-vs-stochastics-volatility-comparison", "N165-relative-strength-index-rsi-overboughtoversold-levels", "R177-filtered-candle-patterns-oscillator-alternatives"]
seed_id: reversal_pattern_oscillator
tags: [insight, discovery, knowledge-evolution]
---

# RSI Filter for Candle Patterns via Low Volatility

## Discovery Summary

Note C149 states RSI is less volatile and reaches extremes less frequently than stochastics, with best signals when both are in extremes. N165 defines RSI overbought (>70) and oversold (<30) levels. R177 specifies that any oscillator can filter candle patterns, but must be in its presignal area. Combining these, RSI becomes a superior filter for reversal candle patterns because its lower volatility means extreme readings are rarer, reducing false signals while still meeting the filter requirement from R177.

## Trading Implication

Only act on reversal candle patterns when RSI is above 70 (overbought) or below 30 (oversold), ignoring stochastics-based signals to reduce noise.

## Supporting Notes

- [[C149-rsi-vs-stochastics-volatility-comparison]]
- [[N165-relative-strength-index-rsi-overboughtoversold-levels]]
- [[R177-filtered-candle-patterns-oscillator-alternatives]]

## Connection Type

**creates_filter** — Actionability score: 4/5
