---
type: insight
date: 2026-09-08
actionability: 4
connection_type: creates_filter
domains: [concepts, risk-guidelines, rules]
sources: ["C245-stop-order", "RG035-combining-technical-factors-with-money-management-for-stop-p", "EN071-pivot-point-buy-signal-rules"]
seed_id: prior_swing_low_stop
tags: [insight, discovery, knowledge-evolution]
topic: knowledge
confidence: high
has_quotes: false
source: unknown
---
# When Intraday Pivot Stops Violate 3:1 Reward Ratios

## Discovery Summary

The EN071 pivot-point buy signal rules specify placing a protective stop below the current day's low after entry, while RG035 requires stops at valid technical levels and implies position sizing must respect a reward/risk framework. Conflict arises when the current day's low stop distance exceeds the technical support level, forcing an oversized risk that violates a 3:1 reward/risk requirement unless the profit target is proportionally extended beyond what the pivot setup normally provides. The C245 stop order definition confirms slippage could further degrade the actual fill, making the theoretical 3:1 ratio even harder to achieve.

## Trading Implication

Before entering a pivot-point breakout, calculate the stop distance from the current day's low and verify it supports at least a 3:1 reward/risk ratio relative to the next resistance target; if not, either pass on the trade or reduce position size per RG035's money management rule rather than widening the stop.

## Supporting Notes

- [[C245-stop-order]]
- [[RG035-combining-technical-factors-with-money-management-for-stop-p]]
- [[EN071-pivot-point-buy-signal-rules]]

## Connection Type

**creates_filter** — Actionability score: 4/5
