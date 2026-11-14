---
type: insight
date: 2026-11-13
actionability: 4
connection_type: reveals_sequence
domains: [concepts, risk-guidelines, rules]
sources: ["RG023-pf-trailing-stop-adjustment", "C245-stop-order", "EN071-pivot-point-buy-signal-rules"]
seed_id: system_exit_design
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# Exits matter: pivot buy signals need protective then trailing stops

## Discovery Summary

EN071-pivot-point-buy-signal-rules shows that the trade is not defined by the pivot breakout alone; the same rule immediately attaches a protective sell stop below the current day’s low, which is the exit that defines risk. C245-stop-order formalizes stop orders as loss limiters and profit protectors, and RG023-pf-trailing-stop-adjustment completes the sequence by trailing the protective stop below the latest o column in an uptrend after repeat buy signals. This operationalizes Murphy’s insight that exits matter more than entries: the entry trigger is only a start, while stop placement and subsequent trailing determine performance.

## Trading Implication

After a pivot-point buy stop is elected, place a protective sell stop below the current day’s low immediately; as further buy signals appear, trail that stop up below the latest Point & Figure o column rather than trying to improve the entry price.

## Supporting Notes

- [[RG023-pf-trailing-stop-adjustment]]
- [[C245-stop-order]]
- [[EN071-pivot-point-buy-signal-rules]]

## Connection Type

**reveals_sequence** — Actionability score: 4/5
