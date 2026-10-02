---
type: insight
date: 2026-10-01
actionability: 4
connection_type: adds_condition
domains: [concepts, indicators, rules]
sources: ["C149-rsi-vs-stochastics-volatility-comparison", "N165-relative-strength-index-rsi-overboughtoversold-levels", "EN036-rsi-divergence-confirmation"]
seed_id: reversal_pattern_oscillator
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# RSI divergence filters overbought signals in volatility

## Discovery Summary

C149 (RSI vs Stochastics Volatility Comparison) suggests that RSI overbought/oversold levels are less reliable in volatile markets. N165 defines standard RSI levels (70/30). EN036 (RSI Divergence Confirmation) provides a divergence rule. The non-obvious connection is that applying the divergence confirmation from EN036 as a filter on the extremes from N165, especially in high volatility conditions noted in C149, significantly reduces false reversal signals.

## Trading Implication

In volatile markets, only enter reversal trades when RSI is at extreme levels (N165) and confirmed by divergence (EN036); ignore extremes without divergence.

## Supporting Notes

- [[C149-rsi-vs-stochastics-volatility-comparison]]
- [[N165-relative-strength-index-rsi-overboughtoversold-levels]]
- [[EN036-rsi-divergence-confirmation]]

## Connection Type

**adds_condition** — Actionability score: 4/5

## Related Notes
- [[EN036-rsi-divergence-confirmation|RSI Divergence Confirmation]]
