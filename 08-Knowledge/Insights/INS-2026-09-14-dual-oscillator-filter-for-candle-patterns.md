---
type: insight
date: 2026-09-14
actionability: 4
connection_type: creates_filter
domains: [concepts, indicators, rules]
sources: ["C149-rsi-vs-stochastics-volatility-comparison", "N165-relative-strength-index-rsi-overboughtoversold-levels", "R177-filtered-candle-patterns-oscillator-alternatives"]
seed_id: reversal_pattern_oscillator
tags: [insight, discovery, knowledge-evolution]
---

# Dual oscillator filter for candle patterns

## Discovery Summary

The notes from 'RSI vs. Stochastics Volatility Comparison' (C149) indicate that best signals occur when both RSI and Stochastics are simultaneously overbought or oversold. 'Filtered Candle Patterns — Oscillator Alternatives' (R177) states that any oscillator can filter candle patterns if it is in its presignal area. Combining these, using both RSI and Stochastics together as a filter for candle reversal patterns (e.g., requiring RSI >70 and Stochastics >80 for a bearish reversal) provides stronger confirmation than using either alone, as RSI alone reaches extremes less frequently.

## Trading Implication

When a candle reversal pattern appears, only take the trade if both RSI and Stochastics are simultaneously in overbought (for bearish) or oversold (for bullish) territory, thereby reducing false signals.

## Supporting Notes

- [[C149-rsi-vs-stochastics-volatility-comparison]]
- [[N165-relative-strength-index-rsi-overboughtoversold-levels]]
- [[R177-filtered-candle-patterns-oscillator-alternatives]]

## Connection Type

**creates_filter** — Actionability score: 4/5
