---
type: insight
date: 2026-08-22
actionability: 3
connection_type: adds_condition
domains: [edge-conditions, indicators, rules]
sources: ["N039-double-crossover-method-10-and-50-day-combination-for-stocks", "E020-double-crossover-reduces-whipsaws-vs-single-average", "EN028-10-and-50-day-moving-average-crossover"]
seed_id: diversification_position_limit
tags: [insight, discovery, knowledge-evolution]
topic: knowledge
confidence: high
has_quotes: false
source: unknown
---
# Crossover Lag vs Position Sizing: Entry Timing Affects Risk Exposure

## Discovery Summary

E020 explicitly notes that the double crossover method (used in N039 and EN028) lags the market more than a single average, producing later entries and exits. If a trader uses 1% position sizing per HermesForge rules, this lag means the entry price is already degraded from the optimal point, effectively increasing the cost basis relative to the signal origin. The seed question about Murphy's 10-15% per market limit is not directly addressed in these notes, but the lag condition from E020 implies that by the time the 10/50 crossover fires, a portion of the move is already consumed, which affects the risk/reward ratio at entry — relevant to how much capital should be allocated per signal.

## Trading Implication

When using the 10/50 crossover (EN028/N039), account for inherent signal lag by tightening initial stop placement rather than accepting the full 1% position risk at the crossover price, since the entry is already behind the optimal point identified by E020.

## Supporting Notes

- [[N039-double-crossover-method-10-and-50-day-combination-for-stocks]]
- [[E020-double-crossover-reduces-whipsaws-vs-single-average]]
- [[EN028-10-and-50-day-moving-average-crossover]]

## Connection Type

**adds_condition** — Actionability score: 3/5
