---
type: insight
date: 2026-09-29
actionability: 3
connection_type: creates_filter
domains: [concepts, indicators, rules]
sources: ["C149-rsi-vs-stochastics-volatility-comparison", "N165-relative-strength-index-rsi-overboughtoversold-levels", "EN036-rsi-divergence-confirmation"]
seed_id: reversal_pattern_oscillator
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# Volatility-Adjusted RSI Divergence for Reversal Confirmation

## Discovery Summary

C149 notes that RSI and stochastics perform differently under varying volatility regimes, while N165 defines standard overbought/oversold thresholds (70/30). EN036 requires RSI divergence confirmation. Together, they imply that in high volatility, standard RSI thresholds produce false signals, so divergence confirmation should require more extreme RSI levels (e.g., 80/20) or use stochastic crossovers as a secondary filter. This adds a volatility-based precondition before acting on RSI divergence.

## Trading Implication

Assess current volatility (e.g., via ATR) before trading RSI divergence: in high-volatility conditions, wait for RSI to reach 80/20 rather than 70/30, and consider confirming with stochastics to avoid premature reversal entries.

## Supporting Notes

- [[C149-rsi-vs-stochastics-volatility-comparison]]
- [[N165-relative-strength-index-rsi-overboughtoversold-levels]]
- [[EN036-rsi-divergence-confirmation]]

## Connection Type

**creates_filter** — Actionability score: 3/5
