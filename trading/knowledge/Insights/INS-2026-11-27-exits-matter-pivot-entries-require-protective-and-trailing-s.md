---
type: insight
date: 2026-11-27
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
# Exits matter: pivot entries require protective and trailing stops

## Discovery Summary

EN071-pivot-point-buy-signal-rules is usually read as an entry playbook, but its protective sell stops and closing requirements are the exit side that actually controls risk. Murphy's point in C245-stop-order — that stop prices are strongly recommended to limit losses and protect profits — makes the entry trigger secondary. Once the trade is on, RG023-pf-trailing-stop-adjustment converts the initial protective stop into a dynamic exit by raising it below each new P&F o column as repeat buy signals appear. This creates a clear sequence: entry trigger, initial stop placement, then trailing stop management.

## Trading Implication

After a pivot-point buy stop is elected, immediately place the specified protective stop, then trail it using the P&F o-column method as the trend continues instead of holding a static stop.

## Supporting Notes

- [[RG023-pf-trailing-stop-adjustment]]
- [[C245-stop-order]]
- [[EN071-pivot-point-buy-signal-rules]]

## Connection Type

**reveals_sequence** — Actionability score: 4/5
