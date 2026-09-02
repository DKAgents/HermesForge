---
type: insight
date: 2026-09-02
actionability: 4
connection_type: creates_filter
domains: [concepts, indicators, rules]
sources: ["C149-rsi-vs-stochastics-volatility-comparison", "N165-relative-strength-index-rsi-overboughtoversold-levels", "R177-filtered-candle-patterns-oscillator-alternatives"]
seed_id: reversal_pattern_oscillator
tags: [insight, discovery, knowledge-evolution]
---

# RSI-Stochastics Alignment Filters Reversal Patterns

## Discovery Summary

C149 notes that the best oscillator signals come when RSI and Stochastics are simultaneously overbought or oversold. N165 defines RSI's overbought/oversold zones as above 70 and below 30. R177 generalizes that any oscillator in its presignal area can validate candle reversal patterns. Combining these: a candle reversal pattern is most reliably confirmed when both RSI (in its 70/30 zones) and Stochastics agree on extreme territory.

## Trading Implication

Before acting on any reversal candle pattern, require confirmation that both RSI and Stochastics are simultaneously in their respective overbought or oversold zones—not just one oscillator. This dual-oscillator alignment filters out lower-probability candle signals and reduces false entries.

## Supporting Notes

- [[C149-rsi-vs-stochastics-volatility-comparison]]
- [[N165-relative-strength-index-rsi-overboughtoversold-levels]]
- [[R177-filtered-candle-patterns-oscillator-alternatives]]

## Connection Type

**creates_filter** — Actionability score: 4/5
