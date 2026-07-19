---
type: insight
date: 2026-07-19
actionability: 4
connection_type: creates_filter
domains: [concepts, indicators, rules]
sources: ["C149-rsi-vs-stochastics-volatility-comparison", "N165-relative-strength-index-rsi-overboughtoversold-levels", "R177-filtered-candle-patterns-oscillator-alternatives"]
seed_id: reversal_pattern_oscillator
tags: [insight, discovery, knowledge-evolution]
---

# Dual Oscillator Confirmation Gate for Candle Reversal Entries

## Discovery Summary

C149 establishes that RSI and Stochastics reach extremes at different frequencies — RSI less often, Stochastics more often — and that their simultaneous extreme readings produce the best signals. R177 states that any oscillator in its overbought/oversold zone can filter candle reversal patterns, but only specifies a single oscillator as the requirement. Combining these two notes creates a stricter, dual-oscillator filter: a candle reversal pattern should only be acted upon when BOTH RSI (per N165, above 70 or below 30) AND Stochastics are simultaneously in their extreme zones. Because RSI reaches extremes less frequently (C149), requiring both oscillators to confirm simultaneously raises the bar and reduces false signals beyond what either oscillator alone would provide.

## Trading Implication

A trader should require both RSI and Stochastics to be in overbought or oversold territory simultaneously before treating a candle reversal pattern as a valid trade signal, using the dual-extreme condition as a higher-conviction entry filter that single-oscillator rules would miss.

## Supporting Notes

- [[C149-rsi-vs-stochastics-volatility-comparison]]
- [[N165-relative-strength-index-rsi-overboughtoversold-levels]]
- [[R177-filtered-candle-patterns-oscillator-alternatives]]

## Connection Type

**creates_filter** — Actionability score: 4/5
