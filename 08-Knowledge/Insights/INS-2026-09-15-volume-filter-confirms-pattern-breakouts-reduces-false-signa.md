---
type: insight
date: 2026-09-15
actionability: 4
connection_type: adds_condition
domains: [concepts, indicators, trading_rules]
sources: ["EN008-volume-confirmation-at-pattern-completion", "N013-volume-as-a-filter-for-false-breakouts", "C324-confirmation"]
seed_id: vol_confirm_risk
tags: [insight, discovery, knowledge-evolution]
---

# Volume Filter Confirms Pattern Breakouts, Reduces False Signals

## Discovery Summary

EN008 states that pattern completion requires volume expansion to confirm validity, while N013 specifies that a valid upside breakout needs heavy volume and warns that light-volume breakouts may fail, especially if followed by heavy-volume decline. C324 defines confirmation as multiple factors agreeing; here, price breakout plus volume expansion confirms the signal. Together, they form a two-step rule: require volume on the breakout, and treat a subsequent heavy-volume decline as invalidation.

## Trading Implication

Only trade a breakout if volume on the breakout day is above average; if the breakout occurs on light volume, either stand aside or tighten the stop, and exit immediately if price reverses on heavy volume.

## Supporting Notes

- [[EN008-volume-confirmation-at-pattern-completion]]
- [[N013-volume-as-a-filter-for-false-breakouts]]
- [[C324-confirmation]]

## Connection Type

**adds_condition** — Actionability score: 4/5
