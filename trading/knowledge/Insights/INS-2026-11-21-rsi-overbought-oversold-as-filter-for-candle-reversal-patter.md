---
type: insight
date: 2026-11-21
actionability: 4
connection_type: creates_filter
domains: [indicators, oscillator filtering, patterns, trading rules]
sources: ["C149-rsi-vs-stochastics-volatility-comparison", "N165-relative-strength-index-rsi-overboughtoversold-levels", "R177-filtered-candle-patterns-oscillator-alternatives"]
seed_id: reversal_pattern_oscillator
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# RSI overbought/oversold as filter for candle reversal patterns

## Discovery Summary

R177-Filtered Candle Patterns states any oscillator can filter candle patterns if it is in its presignal overbought/oversold area. N165 defines RSI overbought as above 70 and oversold as below 30, with divergences warning of reversals. C149 adds that RSI is less volatile than stochastics, so RSI extremes are rarer and more meaningful; requiring RSI to be in an extreme zone before acting on a candle reversal pattern reduces false signals. The strongest confirmation occurs when both RSI and stochastics are simultaneously overbought or oversold.

## Trading Implication

Do not act on a candle reversal pattern unless RSI is above 70 for bearish reversals or below 30 for bullish reversals. If using stochastics, wait for both oscillators to be in the same extreme zone before entering.

## Supporting Notes

- [[C149-rsi-vs-stochastics-volatility-comparison]]
- [[N165-relative-strength-index-rsi-overboughtoversold-levels]]
- [[R177-filtered-candle-patterns-oscillator-alternatives]]

## Connection Type

**creates_filter** — Actionability score: 4/5
