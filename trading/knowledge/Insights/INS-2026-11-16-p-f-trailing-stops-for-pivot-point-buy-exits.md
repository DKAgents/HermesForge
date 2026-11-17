---
type: insight
date: 2026-11-16
actionability: 4
connection_type: adds_condition
domains: [concepts, indicators, risk-guidelines, trading rules]
sources: ["RG023-pf-trailing-stop-adjustment", "C245-stop-order", "EN071-pivot-point-buy-signal-rules"]
seed_id: system_exit_design
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# P&F trailing stops for pivot point buy exits

## Discovery Summary

EN071-pivot-point-buy-signal-rules defines an entry and initial protective stop but does not specify how to trail that stop as the trade moves in your favor. RG023-pf-trailing-stop-adjustment fills that gap: once a pivot buy is elected, a trader can raise the protective sell stop to just below the latest P&F o column, using the trailing-stop concept reinforced by C245-stop-order. This operationalizes Murphy's point that stops/exits deserve as much attention as entries by converting EN071's point-in-time entry into a continuously managed exit.

## Trading Implication

After an EN071 pivot-point long entry, use RG023's method: raise the sell stop to just below each new P&F o column as the uptrend persists, rather than leaving the stop at the initial day-low reference.

## Supporting Notes

- [[RG023-pf-trailing-stop-adjustment]]
- [[C245-stop-order]]
- [[EN071-pivot-point-buy-signal-rules]]

## Connection Type

**adds_condition** — Actionability score: 4/5
