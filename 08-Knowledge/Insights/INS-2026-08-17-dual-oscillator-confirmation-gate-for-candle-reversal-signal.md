---
type: insight
date: 2026-08-17
actionability: 4
connection_type: creates_filter
domains: [concepts, indicators, rules]
sources: ["C149-rsi-vs-stochastics-volatility-comparison", "N165-relative-strength-index-rsi-overboughtoversold-levels", "R177-filtered-candle-patterns-oscillator-alternatives"]
seed_id: reversal_pattern_oscillator
tags: [insight, discovery, knowledge-evolution]
---

# Dual Oscillator Confirmation Gate for Candle Reversal Signals

## Discovery Summary

C149 establishes that RSI and Stochastics reach extremes at different frequencies, with the best signals occurring when both are simultaneously overbought or oversold. R177 states that any oscillator can filter candle patterns, but only when in its presignal extreme zone. Combining these: requiring BOTH RSI (above 70 / below 30 per N165) AND Stochastics to be in extreme territory before validating a candle reversal pattern creates a higher-confidence dual-confirmation gate. This leverages the differing volatility characteristics noted in C149 — since RSI reaches extremes less often, simultaneous RSI + Stochastics extremes represent a rarer, higher-quality filter than using either oscillator alone.

## Trading Implication

A trader should only act on candle reversal patterns when BOTH RSI crosses into overbought (>70) or oversold (<30) territory AND Stochastics is simultaneously in its extreme zone, treating the RSI threshold as the more demanding and therefore more selective filter gate.

## Supporting Notes

- [[C149-rsi-vs-stochastics-volatility-comparison]]
- [[N165-relative-strength-index-rsi-overboughtoversold-levels]]
- [[R177-filtered-candle-patterns-oscillator-alternatives]]

## Connection Type

**creates_filter** — Actionability score: 4/5
