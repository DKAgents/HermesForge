---
type: insight
date: 2026-10-15
actionability: 4
connection_type: adds_condition
domains: [concepts, indicators]
sources: ["C149-rsi-vs-stochastics-volatility-comparison", "N165-relative-strength-index-rsi-overboughtoversold-levels"]
seed_id: reversal_pattern_oscillator
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# Volatility-Adjusted RSI Levels Confirm Reversals

## Discovery Summary

C149 compares RSI and Stochastics under varying volatility, indicating that RSI's extreme readings are relative to market conditions. N165 defines conventional overbought/oversold thresholds (e.g., 70/30). By adding a volatility condition, a reversal pattern should only be confirmed when RSI reaches a threshold adjusted for current volatility—e.g., lower thresholds in low-volatility regimes, higher in high-volatility regimes—rather than relying on fixed levels. This improves the oscillator's confirmation power for reversals.

## Trading Implication

Measure current volatility (ATR or Bollinger Band width) and scale RSI overbought/oversold thresholds accordingly when validating reversal patterns.

## Supporting Notes

- [[C149-rsi-vs-stochastics-volatility-comparison]]
- [[N165-relative-strength-index-rsi-overboughtoversold-levels]]

## Connection Type

**adds_condition** — Actionability score: 4/5

## Related Notes
- [[C124-bollinger-band-width-as-volatility-measure|Bollinger Band Width as Volatility Measure]]
