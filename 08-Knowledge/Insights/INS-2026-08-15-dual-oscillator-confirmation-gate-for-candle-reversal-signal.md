---
type: insight
date: 2026-08-15
actionability: 4
connection_type: creates_filter
domains: [concepts, indicators, rules]
sources: ["C149-rsi-vs-stochastics-volatility-comparison", "N165-relative-strength-index-rsi-overboughtoversold-levels", "R177-filtered-candle-patterns-oscillator-alternatives"]
seed_id: reversal_pattern_oscillator
tags: [insight, discovery, knowledge-evolution]
---

# Dual Oscillator Confirmation Gate for Candle Reversal Signals

## Discovery Summary

C149 establishes that RSI and Stochastics reach extremes at different frequencies, with the best signals occurring when both are simultaneously overbought/oversold. R177 extends this by allowing any oscillator — including RSI — to filter candle reversal patterns, requiring presignal territory before a candle pattern is considered valid. N165 defines the specific RSI thresholds (above 70 / below 30) that constitute overbought/oversold. Together, these three notes support a dual-oscillator filter: a candle reversal pattern is only acted upon when BOTH RSI (above 70 or below 30) AND Stochastics are simultaneously in their extreme zones, reducing false signals from either oscillator alone.

## Trading Implication

A trader should only enter on a candle reversal pattern when both RSI (>70 or <30 per N165) and Stochastics are simultaneously in overbought or oversold territory, using this dual-confirmation gate from C149 as the filter mechanism described in R177 — ignoring candle signals when only one oscillator is in extreme territory.

## Supporting Notes

- [[C149-rsi-vs-stochastics-volatility-comparison]]
- [[N165-relative-strength-index-rsi-overboughtoversold-levels]]
- [[R177-filtered-candle-patterns-oscillator-alternatives]]

## Connection Type

**creates_filter** — Actionability score: 4/5
