---
type: insight
date: 2026-09-09
actionability: 4
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
# Dual Oscillator Overbought/Oversold Confirmation for Candle Patterns

## Discovery Summary

Note C149 states that RSI is less volatile and the best oscillator signals occur when both RSI and Stochastics are simultaneously overbought or oversold. Note R177 establishes that any oscillator can filter candle reversal patterns by requiring the oscillator to be in its presignal (overbought/oversold) area. Combining these, a stronger filter emerges: require both RSI and Stochastics to be extreme before acting on a reversal candle pattern, not just one oscillator.

## Trading Implication

Only take a reversal candle pattern as valid when both RSI (14) and Stochastics %D are in overbought (>70 on RSI, >80 on Stochastics) or oversold (<30, <20) territory simultaneously.

## Supporting Notes

- [[C149-rsi-vs-stochastics-volatility-comparison]]
- [[N165-relative-strength-index-rsi-overboughtoversold-levels]]
- [[R177-filtered-candle-patterns-oscillator-alternatives]]

## Connection Type

**creates_filter** — Actionability score: 4/5
