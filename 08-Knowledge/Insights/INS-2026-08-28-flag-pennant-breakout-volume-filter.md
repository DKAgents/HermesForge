---
type: insight
date: 2026-08-28
actionability: 4
connection_type: adds_condition
domains: [indicators, patterns, rules]
sources: ["N043-flag-and-pennant-summary-characteristics", "R082-breakouts-must-be-accompanied-by-heavy-volume", "N013-volume-as-a-filter-for-false-breakouts"]
seed_id: vol_diverge_stop
tags: [insight, discovery, knowledge-evolution]
topic: knowledge
confidence: high
has_quotes: false
source: unknown
---
# Flag/Pennant Breakout Volume Filter

## Discovery Summary

N043 states that flags and pennants should break out on heavy volume. R082 generalizes that all pattern breakouts require heavy volume for validity. N013 specifies that a light-volume upside breakout is a bull trap, and a subsequent decline on heavy volume confirms the false breakout. Combined, if a flag or pennant breaks out on light volume and then reverses on heavy volume, the setup is invalidated with a high-confidence negative signal.

## Trading Implication

If a flag or pennant breakout occurs on light volume, treat it as suspect; if price then declines on heavy volume, exit any long positions immediately and consider a short entry.

## Supporting Notes

- [[N043-flag-and-pennant-summary-characteristics]]
- [[R082-breakouts-must-be-accompanied-by-heavy-volume]]
- [[N013-volume-as-a-filter-for-false-breakouts]]

## Connection Type

**adds_condition** — Actionability score: 4/5
