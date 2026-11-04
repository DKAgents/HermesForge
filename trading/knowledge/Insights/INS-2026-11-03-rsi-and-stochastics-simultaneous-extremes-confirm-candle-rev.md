---
type: insight
date: 2026-11-03
actionability: 4
connection_type: creates_filter
domains: [concepts, indicators, patterns, trading rules]
sources: ["C149-rsi-vs-stochastics-volatility-comparison", "N165-relative-strength-index-rsi-overboughtoversold-levels", "R177-filtered-candle-patterns-oscillator-alternatives"]
seed_id: reversal_pattern_oscillator
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# RSI and Stochastics Simultaneous Extremes Confirm Candle Reversals

## Discovery Summary

R177-Filtered Candle Patterns — Oscillator Alternatives states any oscillator can filter candle patterns, but the oscillator must be in its presignal overbought/oversold area. C149-rsi-vs-stochastics-volatility-comparison adds that RSI is less volatile and reaches extremes less frequently than stochastics, and that the best signals occur when both oscillators are simultaneously overbought or oversold. N165-relative-strength-index-rsi-overboughtoversold-levels supplies the concrete RSI thresholds of 70 and 30. Therefore, the strongest candle-reversal filter is a simultaneous RSI and stochastic extreme, with RSI's rarer extremes reducing false signals.

## Trading Implication

When a candle reversal pattern appears, only take it if RSI is above 70 (or below 30) and Stochastics is simultaneously in its overbought/oversold zone; treat single-oscillator extremes as weaker signals.

## Supporting Notes

- [[C149-rsi-vs-stochastics-volatility-comparison]]
- [[N165-relative-strength-index-rsi-overboughtoversold-levels]]
- [[R177-filtered-candle-patterns-oscillator-alternatives]]

## Connection Type

**creates_filter** — Actionability score: 4/5
