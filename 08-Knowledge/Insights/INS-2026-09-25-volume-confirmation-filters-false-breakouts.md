---
type: insight
date: 2026-09-25
actionability: 4
connection_type: creates_filter
domains: [concepts, indicators, rules]
sources: ["EN008-volume-confirmation-at-pattern-completion", "N013-volume-as-a-filter-for-false-breakouts", "C324-confirmation"]
seed_id: vol_confirm_risk
tags: [insight, discovery, knowledge-evolution]
---

# Volume confirmation filters false breakouts

## Discovery Summary

EN008 (Volume Confirmation at Pattern Completion) and N013 (Volume as a Filter for False Breakouts) both require increased volume on valid upside breakouts, warning that light volume suggests a false breakout. C324 (Confirmation) broadly defines confirmation as multiple factors agreeing—here, price and volume. Together, they establish a concrete filter: a breakout must have heavy volume to be considered valid, reducing false entries.

## Trading Implication

Only enter a breakout trade when volume expands noticeably above its recent average; if volume is light, treat the breakout as suspect and avoid entry or wait for subsequent heavy-volume follow-through.

## Supporting Notes

- [[EN008-volume-confirmation-at-pattern-completion]]
- [[N013-volume-as-a-filter-for-false-breakouts]]
- [[C324-confirmation]]

## Connection Type

**creates_filter** — Actionability score: 4/5
