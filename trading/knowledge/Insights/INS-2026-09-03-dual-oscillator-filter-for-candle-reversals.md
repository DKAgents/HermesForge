---
type: insight
date: 2026-09-03
actionability: 4
connection_type: adds_condition
domains: [concepts, indicators, rules]
sources: ["C149-rsi-vs-stochastics-volatility-comparison", "N165-relative-strength-index-rsi-overboughtoversold-levels", "R177-filtered-candle-patterns-oscillator-alternatives"]
seed_id: reversal_pattern_oscillator
tags: [insight, discovery, knowledge-evolution]
topic: knowledge
confidence: high
has_quotes: false
source: unknown
---
# Dual Oscillator Filter for Candle Reversals

## Discovery Summary

Rule R177 states any oscillator can filter candle patterns and must be in its overbought/oversold area before a reversal pattern is valid. Note C149 specifies that RSI and stochastics give the best signals when both are simultaneously in overbought or oversold territory. By combining these, a stricter filter emerges: for a candle reversal pattern to be considered high-confidence, both RSI (per N165 levels above 70/below 30) and stochastics must be in the same extreme zone, not just one oscillator.

## Trading Implication

Only act on reversal candle patterns when both RSI and stochastics confirm overbought or oversold conditions simultaneously, discarding patterns that meet only one oscillator's extreme reading.

## Supporting Notes

- [[C149-rsi-vs-stochastics-volatility-comparison]]
- [[N165-relative-strength-index-rsi-overboughtoversold-levels]]
- [[R177-filtered-candle-patterns-oscillator-alternatives]]

## Connection Type

**adds_condition** — Actionability score: 4/5
