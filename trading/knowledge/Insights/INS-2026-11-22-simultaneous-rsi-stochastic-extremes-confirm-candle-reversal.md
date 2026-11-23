---
type: insight
date: 2026-11-22
actionability: 4
connection_type: adds_condition
domains: [concepts, indicators, rules]
sources: ["C149-rsi-vs-stochastics-volatility-comparison", "N165-relative-strength-index-rsi-overboughtoversold-levels", "R177-filtered-candle-patterns-oscillator-alternatives"]
seed_id: reversal_pattern_oscillator
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# Simultaneous RSI-Stochastic Extremes Confirm Candle Reversals

## Discovery Summary

C149 notes that RSI is less volatile and reaches extremes less frequently than stochastics, and that the best signals occur when both oscillators are simultaneously overbought or oversold. R177 states that any oscillator can filter candle patterns, but only if it is already in its presignal overbought/oversold area. Combining these ideas adds a condition to R177's filter: a candle reversal pattern is most valid when both RSI (per N165, above 70 or below 30) and stochastics are simultaneously in extreme territory. N165 also adds that RSI divergence at these extremes warns of a possible trend reversal, strengthening the confirmation.

## Trading Implication

Before acting on a candle reversal pattern, require both RSI and Stochastics to be simultaneously overbought (for tops) or oversold (for bottoms); ignore signals confirmed by only one oscillator. Use RSI divergence at these extremes as an additional reversal warning.

## Supporting Notes

- [[C149-rsi-vs-stochastics-volatility-comparison]]
- [[N165-relative-strength-index-rsi-overboughtoversold-levels]]
- [[R177-filtered-candle-patterns-oscillator-alternatives]]

## Connection Type

**adds_condition** — Actionability score: 4/5
