---
type: insight
date: 2026-10-02
actionability: 3
connection_type: adds_condition
domains: [concepts, rules]
sources: ["EN008-volume-confirmation-at-pattern-completion", "C324-confirmation"]
seed_id: vol_confirm_risk
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# Volume Confirmation and Sizing Limits

## Discovery Summary

Rule EN008 requires volume confirmation at pattern completion before entry. Concept C324 defines confirmation as a threshold validation. Together, they imply that volume confirmation is a necessary condition for full position sizing; when volume fails confirmation, position size must be reduced to maintain risk controls.

## Trading Implication

Always confirm volume using EN008 criteria before sizing a position. If volume is not confirmed, automatically scale down position size (e.g., by 50% or to a fixed minimal lot) to compensate.

## Supporting Notes

- [[EN008-volume-confirmation-at-pattern-completion]]
- [[C324-confirmation]]

## Connection Type

**adds_condition** — Actionability score: 3/5
