---
type: insight
date: 2026-11-25
actionability: 4
connection_type: confirms_risk_rule
domains: [concepts, risk-guidelines, rules]
sources: ["RG023-pf-trailing-stop-adjustment", "C245-stop-order", "EN071-pivot-point-buy-signal-rules"]
seed_id: system_exit_design
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: Murphy - Technical Analysis of the Financial Markets
---
# Exits matter: Stop placement rules operationalize Murphy's insight

## Discovery Summary

C245 quotes Murphy's emphasis on stop prices to protect profits, reinforcing that exit management is critical. EN071 specifies a concrete pivot-point-based entry with a protective stop under today's low or open, while RG023 provides a trailing stop method that adjusts stops with trend continuation (based on P&F columns). Together, these rules operationalize Murphy's principle by giving systematic stop placement techniques that protect profits and limit losses.

## Trading Implication

Use EN071's protective stop placement for initial entries, then apply RG023's trailing stop method (raising to below latest o column in uptrend) to protect accumulated profits as the trend continues.

## Supporting Notes

- [[RG023-pf-trailing-stop-adjustment]]
- [[C245-stop-order]]
- [[EN071-pivot-point-buy-signal-rules]]

## Connection Type

**confirms_risk_rule** — Actionability score: 4/5

## Related Notes
- [[INS-2026-09-16-volume-confirmed-breakout-stop-placement-rule|Volume-Confirmed Breakout Stop Placement Rule]]
