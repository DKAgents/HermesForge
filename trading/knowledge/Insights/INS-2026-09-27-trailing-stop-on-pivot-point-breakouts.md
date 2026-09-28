---
type: insight
date: 2026-09-27
actionability: 4
connection_type: reveals_sequence
domains: [concepts, risk-guidelines, rules]
sources: ["RG023-pf-trailing-stop-adjustment", "C245-stop-order", "EN071-pivot-point-buy-signal-rules"]
seed_id: system_exit_design
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# Trailing stop on pivot point breakouts

## Discovery Summary

Pivot Point Buy Signal Rules (EN071) define entry triggers and initial stop placement below the day's low, but not how to trail the stop as the trend extends. P&F Trailing Stop Adjustment (RG023) provides a concrete method: raise the protective stop to just below the latest o column after each new buy signal in an uptrend. This combines Murphy's exit emphasis (C245) with a systematic trailing technique to lock in profits, addressing the gap in EN071's exit rules.

## Trading Implication

After a pivot point buy stop is elected and the trade moves in your favor, trail your sell stop up to just below each new o column generated on a point-and-figure chart, rather than keeping the initial stop fixed.

## Supporting Notes

- [[RG023-pf-trailing-stop-adjustment]]
- [[C245-stop-order]]
- [[EN071-pivot-point-buy-signal-rules]]

## Connection Type

**reveals_sequence** — Actionability score: 4/5
