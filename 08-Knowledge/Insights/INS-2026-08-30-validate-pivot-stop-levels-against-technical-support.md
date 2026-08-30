---
type: insight
date: 2026-08-30
actionability: 4
connection_type: creates_filter
domains: [breakout rules, order types, risk management]
sources: ["C245-stop-order", "RG035-combining-technical-factors-with-money-management-for-stop-p", "EN071-pivot-point-buy-signal-rules"]
seed_id: prior_swing_low_stop
tags: [insight, discovery, knowledge-evolution]
---

# Validate Pivot Stop Levels Against Technical Support

## Discovery Summary

RG035 requires protective stops to be placed at valid technical levels, but EN071 sets them mechanically at the current day's low or open, which may not coincide with support. This conflict means the pivot point rule can produce stops that undermine the risk guideline, so a trader should filter EN071 setups by confirming those levels align with technical support to satisfy both.

## Trading Implication

Before entering a pivot point buy signal, verify today's low (or open for late entry) is below a clear support level; if not, skip the trade or adjust the stop to the nearest support and recalculate position size per RG035.

## Supporting Notes

- [[C245-stop-order]]
- [[RG035-combining-technical-factors-with-money-management-for-stop-p]]
- [[EN071-pivot-point-buy-signal-rules]]

## Connection Type

**creates_filter** — Actionability score: 4/5
