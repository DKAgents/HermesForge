---
type: insight
date: 2026-11-20
actionability: 4
connection_type: creates_filter
domains: [indicators, patterns, risk_guidelines, trading_rules]
sources: ["N013-volume-as-a-filter-for-false-breakouts", "R052-filters-for-confirming-breakouts", "N028-bull-trap-false-upside-breakout"]
seed_id: breakout_volume_risk
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# Volume-Confirmed Breakout Filter and Stop Placement

## Discovery Summary

R052-filters-for-confirming-breakouts lists close/penetration/two-day/Friday filters for breakout confirmation. N013-volume-as-a-filter-for-false-breakouts adds that a valid upside breakout must be on heavy volume, while light-volume breakouts are suspect. N028-bull-trap-false-upside-breakout defines the trap as a light-volume upside breakout followed by a heavy-volume decline, so combining these notes creates a composite filter: only trade breakouts that clear resistance on a close with heavy volume; otherwise treat them as false and manage stops accordingly.

## Trading Implication

Traders should require heavy volume along with R052's close/penetration filters before treating a breakout as valid; if a breakout occurs on light volume, treat it as a potential bull trap and set a protective stop just below the breakout level, exiting on the heavy-volume decline.

## Supporting Notes

- [[N013-volume-as-a-filter-for-false-breakouts]]
- [[R052-filters-for-confirming-breakouts]]
- [[N028-bull-trap-false-upside-breakout]]

## Connection Type

**creates_filter** — Actionability score: 4/5
