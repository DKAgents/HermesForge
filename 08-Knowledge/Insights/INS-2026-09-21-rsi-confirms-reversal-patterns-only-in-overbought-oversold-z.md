---
type: insight
date: 2026-09-21
actionability: 4
connection_type: adds_condition
domains: [concepts, indicators, patterns, rules]
sources: ["C149-rsi-vs-stochastics-volatility-comparison", "N165-relative-strength-index-rsi-overboughtoversold-levels", "R177-filtered-candle-patterns-oscillator-alternatives"]
seed_id: reversal_pattern_oscillator
tags: [insight, discovery, knowledge-evolution]
topic: knowledge
confidence: high
has_quotes: false
source: unknown
---
# RSI Confirms Reversal Patterns Only in Overbought/Oversold Zones

## Discovery Summary

R177 (Filtered Candle Patterns) states that any oscillator can filter candle patterns, but only if it is in its presignal (overbought or oversold) area. N165 (RSI Overbought/Oversold Levels) defines those areas as above 70 or below 30. C149 (RSI vs. Stochastics Volatility) adds that RSI is less volatile than stochastics, meaning its overbought/oversold extremes are rarer and thus more meaningful when they do occur. Therefore, using RSI at extreme levels (e.g., >70 or <30) as a filter for candle reversal patterns provides a stronger confirmation than using a more volatile oscillator like stochastics, which may generate more false signals.

## Trading Implication

When a bullish or bearish candlestick reversal pattern appears, only take the trade if RSI is simultaneously below 30 (for bullish) or above 70 (for bearish), as these extremes align with RSI's presignal zones and reduce false signals. Avoid entering if RSI is not in its extreme territory, even if the pattern looks valid.

## Supporting Notes

- [[C149-rsi-vs-stochastics-volatility-comparison]]
- [[N165-relative-strength-index-rsi-overboughtoversold-levels]]
- [[R177-filtered-candle-patterns-oscillator-alternatives]]

## Connection Type

**adds_condition** — Actionability score: 4/5
