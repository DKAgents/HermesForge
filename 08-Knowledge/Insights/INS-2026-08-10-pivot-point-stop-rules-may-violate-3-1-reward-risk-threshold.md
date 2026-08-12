---
type: insight
date: 2026-08-10
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
# Pivot Point Stop Rules May Violate 3:1 Reward/Risk Threshold

## Discovery Summary

EN071 specifies that a protective sell stop is placed below the current day's low after a buy stop is elected above the previous day's high — this stop distance is mechanically fixed by intraday price range, not by reward/risk ratio. RG035 requires stops to be placed at valid technical levels AND satisfy money management criteria (max 5% risk on total account). If the current day's low is far below entry, the fixed stop in EN071 may consume more than the allowed 5% risk, forcing a position size reduction that may then make the trade's reward insufficient to meet a 3:1 ratio. C245 further notes that fast markets can produce fills beyond the stop price, widening realized risk beyond the technical level chosen.

## Trading Implication

Before entering a Pivot Point buy signal per EN071, calculate the distance from the buy stop trigger to today's low; if that distance exceeds the 5% risk budget from RG035 or fails to deliver 3:1 reward/risk at a logical target, skip the trade or reduce size — do not override the stop to fit the ratio.

## Supporting Notes

- [[C245-stop-order]]
- [[RG035-combining-technical-factors-with-money-management-for-stop-p]]
- [[EN071-pivot-point-buy-signal-rules]]

## Connection Type

**resolves_conflict** — Actionability score: 4/5
