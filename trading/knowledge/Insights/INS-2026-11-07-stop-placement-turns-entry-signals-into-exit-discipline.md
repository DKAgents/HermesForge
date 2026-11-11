---
type: insight
date: 2026-11-07
actionability: 4
connection_type: confirms_risk_rule
domains: [concepts, risk-guidelines, trading-rules]
sources: ["RG023-pf-trailing-stop-adjustment", "C245-stop-order", "EN071-pivot-point-buy-signal-rules"]
seed_id: system_exit_design
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# Stop placement turns entry signals into exit discipline

## Discovery Summary

Murphy's quote in C245-stop-order that stop prices are strongly recommended to protect profits is operationalized by concrete stop rules in the other notes. RG023-pf-trailing-stop-adjustment shows how to trail stops below the latest o column in an uptrend, while EN071-pivot-point-buy-signal-rules defines protective sell stops below the current day's low/open when a buy stop is elected. This ties exits directly to the same technical levels that trigger entries, making exit management as systematic as entry generation.

## Trading Implication

Define each entry together with its invalidation level before entering, and trail stops mechanically off the same P&F columns, pivot highs/lows, or day structures used for the signal. Treat stop placement as the primary profit-protection mechanism rather than an afterthought.

## Supporting Notes

- [[RG023-pf-trailing-stop-adjustment]]
- [[C245-stop-order]]
- [[EN071-pivot-point-buy-signal-rules]]

## Connection Type

**confirms_risk_rule** — Actionability score: 4/5

## Related Notes
- [[RG020-protective-sell-stops-on-point-and-figure-charts|Protective Sell Stops on Point and Figure Charts]]
