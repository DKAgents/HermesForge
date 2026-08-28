---
type: insight
date: 2026-08-28
actionability: 4
connection_type: creates_filter
domains: [indicators, patterns, trading rules]
sources: ["C149-rsi-vs-stochastics-volatility-comparison", "N165-relative-strength-index-rsi-overboughtoversold-levels", "R177-filtered-candle-patterns-oscillator-alternatives"]
seed_id: reversal_pattern_oscillator
tags: [insight, discovery, knowledge-evolution]
---

# Dual-Oscillator Extreme Zone Filter for Candle Patterns

## Discovery Summary

Note C149 states that the best signals occur when both RSI and Stochastics are simultaneously in overbought or oversold territory. Note R177 expands candle pattern filtering beyond Stochastics, allowing any oscillator to validate patterns when it is in its presignal (overbought/oversold) area. Combining these, a non-obvious filter emerges: requiring both RSI and Stochastics to be in extreme zones simultaneously before acting on a candle reversal pattern, thereby leveraging the lower volatility of RSI and the higher sensitivity of Stochastics for stronger confirmation.

## Trading Implication

Only consider a candle reversal pattern valid if both RSI (e.g., 14-period) and Stochastics %D are in overbought (>70) or oversold (<30) territory at the same time.

## Supporting Notes

- [[C149-rsi-vs-stochastics-volatility-comparison]]
- [[N165-relative-strength-index-rsi-overboughtoversold-levels]]
- [[R177-filtered-candle-patterns-oscillator-alternatives]]

## Connection Type

**creates_filter** — Actionability score: 4/5
