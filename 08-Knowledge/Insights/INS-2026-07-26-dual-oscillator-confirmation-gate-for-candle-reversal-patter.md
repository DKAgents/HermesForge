---
type: insight
date: 2026-07-26
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
# Dual-Oscillator Confirmation Gate for Candle Reversal Patterns

## Discovery Summary

R177-filtered-candle-patterns-oscillator-alternatives establishes that ANY oscillator in its overbought/oversold extreme can serve as a validity filter for candle reversal patterns. C149-rsi-vs-stochastics-volatility-comparison reveals that RSI reaches extremes less frequently than Stochastics, meaning RSI extreme readings are rarer and therefore carry more signal weight. N165-relative-strength-index-rsi-overboughtoversold-levels defines those RSI thresholds precisely (above 70 / below 30). Combining all three: a candle reversal pattern is only acted upon when BOTH Stochastics AND RSI simultaneously occupy their respective extreme zones — the dual-confirmation condition Murphy explicitly identifies as producing the best signals — making RSI the higher-bar secondary filter layered on top of Stochastics.

## Trading Implication

Only enter a candle reversal trade when the pattern is present AND both RSI (>70 overbought / <30 oversold) AND Stochastics are simultaneously in their extreme zones; because RSI reaches extremes less frequently, its presence alongside Stochastics extreme raises signal quality and justifies tighter entries or larger size relative to single-oscillator filtered setups.

## Supporting Notes

- [[C149-rsi-vs-stochastics-volatility-comparison]]
- [[N165-relative-strength-index-rsi-overboughtoversold-levels]]
- [[R177-filtered-candle-patterns-oscillator-alternatives]]

## Connection Type

**adds_condition** — Actionability score: 4/5

## Related
- [[N082-filtered-candle-patterns-stochastics-d-application]] — Stochastics %D presignal area rule for dual-oscillator gate

- [[C183-filtered-candle-patterns-concept]] — See Filtered Candle Patterns for the underlying oscillator-gate methodology.

- [[N062-macd-divergence-analysis]] — See MACD divergence as a directional momentum filter for reversal patterns
