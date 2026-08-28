---
type: insight
date: 2026-07-30
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

C149 establishes that RSI and Stochastics reach extremes independently — RSI less frequently, Stochastics more volatilely — and that simultaneous extreme readings provide the best signals. R177 states that any oscillator in its overbought/oversold zone can filter candle reversal patterns, requiring the presignal condition before a candle pattern is considered valid. Combining these, a trader can require BOTH RSI (above 70 / below 30, per N165) AND Stochastics to be simultaneously in extreme territory before acting on a candle reversal pattern — creating a dual-oscillator confirmation gate that is stricter than single-oscillator filtering.

## Trading Implication

Only trade candle reversal patterns when both RSI (>70 overbought / <30 oversold) AND Stochastics are simultaneously in their extreme zones; this dual-confirmation gate reduces false pattern signals by leveraging RSI's selectivity as an additional filter on top of the standard Stochastics-based candle filter from R177.

## Supporting Notes

- [[C149-rsi-vs-stochastics-volatility-comparison]]
- [[N165-relative-strength-index-rsi-overboughtoversold-levels]]
- [[R177-filtered-candle-patterns-oscillator-alternatives]]

## Connection Type

**creates_filter** — Actionability score: 4/5

## Related
- [[N062-macd-divergence-analysis]] — See N062-macd-divergence-analysis for MACD as potential third oscillator filter

- [[R127-zero-line-crossings-must-align-with-prevailing-trend]] — See R127-zero-line-crossings-must-align-with-prevailing-trend for trend-alignment requirement on oscillator signals

- [[C183-filtered-candle-patterns-concept]] — See C183-filtered-candle-patterns-concept for the foundational candle filtering concept
