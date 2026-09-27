---
type: insight
date: 2026-08-03
actionability: 4
connection_type: creates_filter
domains: [concepts, indicators, rules]
sources: ["EN008-volume-confirmation-at-pattern-completion", "N013-volume-as-a-filter-for-false-breakouts", "C324-confirmation"]
seed_id: vol_confirm_risk
tags: [insight, discovery, knowledge-evolution]
topic: knowledge
confidence: high
has_quotes: false
source: unknown
---
# Volume Confirmation as Binary Entry Gate for Breakout Trades

## Discovery Summary

EN008 establishes that pattern completion requires noticeable volume expansion as a confirming factor, while N013 extends this by specifying the asymmetry: heavy volume validates upside breakouts, but light volume signals a likely bull trap. C324 defines confirmation as requiring multiple market factors to agree, which frames volume not as an optional check but as a mandatory second factor alongside price. Together, these three notes construct a two-condition entry rule: price breaks out AND volume expands — both must be true.

## Trading Implication

A trader should treat light-volume breakouts as disqualified entries, not reduced-size entries — the breakout simply does not meet the confirmation threshold defined by EN008 and N013, so no position should be initiated until volume confirms.

## Supporting Notes

- [[EN008-volume-confirmation-at-pattern-completion]]
- [[N013-volume-as-a-filter-for-false-breakouts]]
- [[C324-confirmation]]

## Connection Type

**creates_filter** — Actionability score: 4/5
