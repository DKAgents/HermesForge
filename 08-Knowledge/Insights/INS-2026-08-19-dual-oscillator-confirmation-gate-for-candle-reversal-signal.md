---
type: insight
date: 2026-08-19
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
# Dual Oscillator Confirmation Gate for Candle Reversal Signals

## Discovery Summary

C149 establishes that RSI and Stochastics reach extremes at different frequencies, with the best signals occurring when both are simultaneously overbought or oversold. R177 states that any oscillator can filter candle reversal patterns, requiring the oscillator to be in its presignal extreme area before a candle pattern is considered valid. Combining these: using BOTH RSI (above 70 / below 30 per N165) AND Stochastics simultaneously in extreme territory as a dual-gate filter for candle reversal patterns is significantly more selective than using either oscillator alone, reducing false pattern signals.

## Trading Implication

A trader should only act on candle reversal patterns when BOTH RSI and Stochastics are simultaneously in overbought (RSI >70) or oversold (RSI <30) territory, treating the dual-oscillator confirmation as a mandatory pre-condition rather than using a single oscillator filter as described in R177.

## Supporting Notes

- [[C149-rsi-vs-stochastics-volatility-comparison]]
- [[N165-relative-strength-index-rsi-overboughtoversold-levels]]
- [[R177-filtered-candle-patterns-oscillator-alternatives]]

## Connection Type

**creates_filter** — Actionability score: 4/5
