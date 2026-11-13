---
type: insight
date: 2026-11-12
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
# Volume-Confirmed Breakouts Avoid Bull Traps and Trigger Exits

## Discovery Summary

N013 and N028 both identify a light-volume upside breakout followed by a heavy-volume decline as a bull trap/false breakout. R052 adds confirmation filters (close, percentage, two-day, Friday close) that reduce premature breakout signals. Together they form a filter: require heavy volume plus a confirmation filter before treating a breakout as valid, and use the heavy-volume decline after a light-volume breakout as an immediate exit/stop trigger.

## Trading Implication

Do not enter a breakout solely on price penetration; wait for volume and R052-style confirmation. If long and a light-volume breakout is followed by heavy-volume decline, exit immediately rather than waiting for a price stop.

## Supporting Notes

- [[N013-volume-as-a-filter-for-false-breakouts]]
- [[R052-filters-for-confirming-breakouts]]
- [[N028-bull-trap-false-upside-breakout]]

## Connection Type

**creates_filter** — Actionability score: 4/5
