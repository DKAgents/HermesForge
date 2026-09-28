---
type: insight
date: 2026-09-27
actionability: 4
connection_type: creates_filter
domains: [trading_concepts, trading_rules, volume_indicators]
sources: ["EN008-volume-confirmation-at-pattern-completion", "N013-volume-as-a-filter-for-false-breakouts", "C324-confirmation"]
seed_id: vol_confirm_risk
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# Volume-Confirmed Breakouts Filter Entries and Flag Reversals

## Discovery Summary

EN008 requires volume expansion at pattern completion, while N013 sharpens this by showing that heavy volume validates upside breakouts and light-volume breakouts are suspect. C324 frames this as confirmation: price and volume must agree. Combined, these rules create an actionable filter: volume confirmation is an entry condition, and a heavy-volume decline after a light-volume breakout signals a false breakout.

## Trading Implication

Enter a breakout only if volume expands; if a light-volume upside breakout is followed by a heavy-volume decline, treat the breakout as failed and avoid or reverse exposure.

## Supporting Notes

- [[EN008-volume-confirmation-at-pattern-completion]]
- [[N013-volume-as-a-filter-for-false-breakouts]]
- [[C324-confirmation]]

## Connection Type

**creates_filter** — Actionability score: 4/5
