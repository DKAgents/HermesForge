---
type: insight
date: 2026-08-12
actionability: 4
connection_type: resolves_conflict
domains: [concepts, risk-guidelines, rules]
sources: ["C245-stop-order", "RG035-combining-technical-factors-with-money-management-for-stop-p", "EN071-pivot-point-buy-signal-rules"]
seed_id: prior_swing_low_stop
tags: [insight, discovery, knowledge-evolution]
topic: knowledge
confidence: high
has_quotes: false
source: unknown
---
# Pivot Point Stop Rules vs. 3:1 Reward/Risk Conflict Filter

## Discovery Summary

EN071 defines a mechanical stop placement rule (below current day's low or under today's open) that is purely time/price-driven, while RG035 requires stops to be placed at valid technical levels AND satisfy a maximum 5% account risk constraint. The conflict arises when the EN071 pivot stop is technically valid but produces a stop distance that yields less than 3:1 reward/risk — either because the stop is too close to generate a meaningful target or the position sizing required by RG035 makes the trade immaterial. C245 reinforces that stop orders may fill beyond the stop price in fast markets, further eroding the reward/risk ratio on tight intraday stops specified in EN071.

## Trading Implication

Before entering an EN071 pivot buy signal, calculate the distance from entry (above prior high) to the EN071 protective stop, then verify the implied target satisfies 3:1 reward/risk and that the resulting position size under RG035's 5% max risk rule is meaningful; skip the trade if either condition fails.

## Supporting Notes

- [[C245-stop-order]]
- [[RG035-combining-technical-factors-with-money-management-for-stop-p]]
- [[EN071-pivot-point-buy-signal-rules]]

## Connection Type

**resolves_conflict** — Actionability score: 4/5
