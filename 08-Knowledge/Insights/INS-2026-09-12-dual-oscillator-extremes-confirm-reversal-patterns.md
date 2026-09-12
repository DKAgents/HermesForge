---
type: insight
date: 2026-09-12
actionability: 4
connection_type: creates_filter
domains: [concepts, indicators, rules]
sources: ["C149-rsi-vs-stochastics-volatility-comparison", "N165-relative-strength-index-rsi-overboughtoversold-levels", "R177-filtered-candle-patterns-oscillator-alternatives"]
seed_id: reversal_pattern_oscillator
tags: [insight, discovery, knowledge-evolution]
---

# Dual Oscillator Extremes Confirm Reversal Patterns

## Discovery Summary

C149 notes that the best signals occur when both RSI and Stochastics are simultaneously in overbought/oversold territory. Rule R177 states any oscillator can filter candle reversal patterns by requiring it to be in a presignal area. Integrating these, a trader can create a high-confidence filter: only act on candle reversal patterns when both RSI (per N165 thresholds: above 70 or below 30) and Stochastics are extreme, using RSI's lower volatility to reduce Stochastics' frequent false extremes.

## Trading Implication

Before entering a trade based on a candle reversal pattern, confirm that both RSI and Stochastics are in overbought/oversold territory simultaneously (e.g., RSI >70 or <30; Stochastics >80 or <20).

## Supporting Notes

- [[C149-rsi-vs-stochastics-volatility-comparison]]
- [[N165-relative-strength-index-rsi-overboughtoversold-levels]]
- [[R177-filtered-candle-patterns-oscillator-alternatives]]

## Connection Type

**creates_filter** — Actionability score: 4/5
