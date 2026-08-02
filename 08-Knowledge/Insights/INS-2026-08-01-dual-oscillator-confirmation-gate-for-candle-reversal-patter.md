---
type: insight
date: 2026-08-01
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
# Dual Oscillator Confirmation Gate for Candle Reversal Patterns

## Discovery Summary

C149 establishes that RSI and Stochastics confirm each other most powerfully when both are simultaneously in overbought or oversold territory. R177 states that any oscillator — explicitly including RSI — can filter candle reversal patterns, but only when the oscillator is in its presignal extreme zone. N165 defines RSI's overbought/oversold thresholds as 70/30. Combining these three notes yields a dual-oscillator filter: a candle reversal pattern is only acted upon when BOTH RSI (>70 or <30) AND Stochastics are simultaneously in their respective extreme zones, creating a higher-confidence confirmation gate than either oscillator alone.

## Trading Implication

A trader should require both RSI (above 70 or below 30 per N165) and Stochastics to be simultaneously in overbought or oversold territory before treating any candle reversal pattern as a valid trade signal, effectively raising the confirmation bar and reducing false entries.

## Supporting Notes

- [[C149-rsi-vs-stochastics-volatility-comparison]]
- [[N165-relative-strength-index-rsi-overboughtoversold-levels]]
- [[R177-filtered-candle-patterns-oscillator-alternatives]]

## Connection Type

**creates_filter** — Actionability score: 4/5
