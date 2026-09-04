---
type: insight
date: 2026-09-04
actionability: 4
connection_type: creates_filter
domains: [concepts, indicators, rules]
sources: ["C149-rsi-vs-stochastics-volatility-comparison", "N165-relative-strength-index-rsi-overboughtoversold-levels", "R177-filtered-candle-patterns-oscillator-alternatives"]
seed_id: reversal_pattern_oscillator
tags: [insight, discovery, knowledge-evolution]
---

# Dual Oscillator Confirmation Filters Reversal Patterns

## Discovery Summary

N165-RSI-overbought/oversold-levels establishes RSI's standard thresholds (>70 overbought, <30 oversold) as reversal warnings. C149-rsi-vs-stochastics-volatility-comparison notes that simultaneous overbought/oversold readings in both RSI and Stochastics produce the best signals. R177-filtered-candle-patterns-oscillator-alternatives generalizes this by stating any oscillator in its presignal area can validate a candle reversal pattern. Combining these: the optimal filter for a reversal pattern confirmation is not just one oscillator in extreme territory, but the alignment of both RSI and Stochastics (or equivalent pair) simultaneously overbought/oversold when the candle pattern forms.

## Trading Implication

Require both RSI and Stochastics to be in overbought/oversold zones concurrently before acting on any candlestick reversal pattern, not just one oscillator as typically done.

## Supporting Notes

- [[C149-rsi-vs-stochastics-volatility-comparison]]
- [[N165-relative-strength-index-rsi-overboughtoversold-levels]]
- [[R177-filtered-candle-patterns-oscillator-alternatives]]

## Connection Type

**creates_filter** — Actionability score: 4/5
