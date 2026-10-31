---
type: insight
date: 2026-10-21
actionability: 3
connection_type: adds_condition
domains: [breakout_patterns, indicators, risk_management, trading_rules]
sources: ["N013-volume-as-a-filter-for-false-breakouts", "R052-filters-for-confirming-breakouts"]
seed_id: breakout_volume_risk
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# Volume-confirmed breakouts; tight stops on low-volume false breaks

## Discovery Summary

N013 establishes volume as a filter for false breakouts, while R052 lists filters for confirming breakout entries. Combined, they imply that a breakout pattern is only valid when volume expands on the break bar; if volume does not confirm, the move is likely a false breakout. This creates a concrete stop-placement rule: when a level breaks on low volume, place the protective stop at or just beyond the breakout level rather than at a normal follow-through distance.

## Trading Implication

Require above-average volume before entering a breakout; if price pierces a level on weak volume, either skip the trade or use a tight stop at the breakout level to limit risk from an expected reversal.

## Supporting Notes

- [[N013-volume-as-a-filter-for-false-breakouts]]
- [[R052-filters-for-confirming-breakouts]]

## Connection Type

**adds_condition** — Actionability score: 3/5
