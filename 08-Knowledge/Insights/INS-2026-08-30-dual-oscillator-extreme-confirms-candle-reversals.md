---
type: insight
date: 2026-08-30
actionability: 5
connection_type: creates_filter
domains: [concepts, indicators, rules]
sources: ["C149-rsi-vs-stochastics-volatility-comparison", "N165-relative-strength-index-rsi-overboughtoversold-levels", "R177-filtered-candle-patterns-oscillator-alternatives"]
seed_id: reversal_pattern_oscillator
tags: [insight, discovery, knowledge-evolution]
topic: knowledge
confidence: high
has_quotes: false
source: unknown
---
# Dual Oscillator Extreme Confirms Candle Reversals

## Discovery Summary

Rule R177 states any oscillator can filter candle patterns, requiring it to be overbought/oversold. Concept C149 notes RSI is less volatile than stochastics and the best signals occur when both oscillators are simultaneously in extreme territory. By combining these, reversal candle patterns are most reliably confirmed when both RSI (>70 or <30 per N165) and stochastics are in their respective overbought/oversold zones, filtering out lower-probability setups.

## Trading Implication

Before acting on any reversal candle pattern, require both RSI and Stochastic %D to be simultaneously overbought or oversold. Ignore patterns where only one oscillator is extreme to reduce false signals.

## Supporting Notes

- [[C149-rsi-vs-stochastics-volatility-comparison]]
- [[N165-relative-strength-index-rsi-overboughtoversold-levels]]
- [[R177-filtered-candle-patterns-oscillator-alternatives]]

## Connection Type

**creates_filter** — Actionability score: 5/5
