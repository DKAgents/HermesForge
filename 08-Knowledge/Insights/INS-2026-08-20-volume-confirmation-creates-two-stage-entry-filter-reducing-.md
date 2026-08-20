---
type: insight
date: 2026-08-20
actionability: 4
connection_type: creates_filter
domains: [indicators, rules]
sources: ["EN008-volume-confirmation-at-pattern-completion", "N013-volume-as-a-filter-for-false-breakouts"]
seed_id: vol_confirm_risk
tags: [insight, discovery, knowledge-evolution]
---

# Volume Confirmation Creates Two-Stage Entry Filter Reducing False Breakouts

## Discovery Summary

EN008 establishes that pattern completion requires noticeable volume expansion as a confirming factor, while N013 extends this by specifying the post-breakout volume behavior: a subsequent decline on heavy volume after a light-volume breakout confirms the breakout was false. Together, these notes create a two-stage volume filter — first at breakout (EN008: heavy volume required), then on any post-breakout pullback (N013: heavy volume decline = exit signal). The combination converts a qualitative confirmation rule into a falsifiable, observable two-event sequence.

## Trading Implication

A trader should require heavy volume at the breakout candle before entering, and immediately reassess the position if any post-entry decline occurs on volume that exceeds the breakout candle's volume — treating this as a confirmed bull trap signal requiring exit or position reduction.

## Supporting Notes

- [[EN008-volume-confirmation-at-pattern-completion]]
- [[N013-volume-as-a-filter-for-false-breakouts]]

## Connection Type

**creates_filter** — Actionability score: 4/5
