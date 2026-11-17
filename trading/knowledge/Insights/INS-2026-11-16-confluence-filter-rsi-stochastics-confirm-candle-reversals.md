---
type: insight
date: 2026-11-16
actionability: 4
connection_type: creates_filter
domains: [candle_patterns, indicators, oscillators, trading_rules]
sources: ["C149-rsi-vs-stochastics-volatility-comparison", "N165-relative-strength-index-rsi-overboughtoversold-levels", "R177-filtered-candle-patterns-oscillator-alternatives"]
seed_id: reversal_pattern_oscillator
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# Confluence Filter: RSI + Stochastics Confirm Candle Reversals

## Discovery Summary

R177 requires an oscillator to be in its presignal overbought/oversold area before a candle reversal pattern is valid. C149 adds that RSI is less volatile and reaches extremes less often, so the best signals occur when RSI and Stochastics are simultaneously in overbought/oversold territory. N165 supplies the standard RSI thresholds above 70/below 30 and notes that divergence at these extremes warns of possible trend reversal. Together they imply a robust candle-pattern filter: dual oscillator extremes rather than any single oscillator reading.

## Trading Implication

Before acting on a bullish or bearish candle reversal pattern, require both RSI and Stochastics to be simultaneously overbought/oversold, and treat RSI divergence as added reversal confirmation. This should reduce false pattern signals.

## Supporting Notes

- [[C149-rsi-vs-stochastics-volatility-comparison]]
- [[N165-relative-strength-index-rsi-overboughtoversold-levels]]
- [[R177-filtered-candle-patterns-oscillator-alternatives]]

## Connection Type

**creates_filter** — Actionability score: 4/5

## Related Notes
- [[INS-2026-09-12-dual-oscillator-extremes-confirm-reversal-patterns|Dual Oscillator Extremes Confirm Reversal Patterns]]
