---
type: insight
date: 2026-10-29
actionability: 4
connection_type: adds_condition
domains: [indicators, patterns, risk management, rules]
sources: ["N043-flag-and-pennant-summary-characteristics", "R082-breakouts-must-be-accompanied-by-heavy-volume", "N013-volume-as-a-filter-for-false-breakouts"]
seed_id: vol_diverge_stop
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# Tighten stops when breakout volume diverges from price

## Discovery Summary

Flag and pennant patterns normally show volume contraction during consolidation and expansion on breakout (N043). R082 requires heavy volume for valid breakouts, and N013 uses volume as a filter against false breakouts. If price moves in the breakout direction but volume diverges by failing to expand, the breakout is suspect, so stops should be tightened rather than left at the normal pattern extreme.

## Trading Implication

On a breakout or trend continuation with weak or declining volume, move stops closer to the entry or just inside the pattern boundary to reduce loss if the move fails.

## Supporting Notes

- [[N043-flag-and-pennant-summary-characteristics]]
- [[R082-breakouts-must-be-accompanied-by-heavy-volume]]
- [[N013-volume-as-a-filter-for-false-breakouts]]

## Connection Type

**adds_condition** — Actionability score: 4/5
