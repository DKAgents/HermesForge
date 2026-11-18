---
type: insight
date: 2026-11-17
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
# Entry stops trigger; protective/trailing stops drive P&L

## Discovery Summary

EN071 uses a buy stop as the entry trigger, but immediately requires a protective sell stop below the day's low (or open in the late-entry variant). C245 reminds that stop orders become market orders and can fill beyond the stop, so the exit stop is where risk is actually controlled. RG023 then shows how that protective stop should be trailed as the trend continues. This turns Murphy's exit-focused insight into a sequence: enter on the EN071 buy stop, protect with the initial stop, then trail using P&F columns.

## Trading Implication

When taking an EN071 pivot buy signal, do not optimize the entry trigger alone; predefine the protective sell stop before entry and trail it per RG023 after the position is filled.

## Supporting Notes

- [[RG023-pf-trailing-stop-adjustment]]
- [[C245-stop-order]]
- [[EN071-pivot-point-buy-signal-rules]]

## Connection Type

**reveals_sequence** — Actionability score: 4/5

## Related Notes
- [[C243-market-order|Market Order]]
- [[C245-stop-order|Stop Order]]
