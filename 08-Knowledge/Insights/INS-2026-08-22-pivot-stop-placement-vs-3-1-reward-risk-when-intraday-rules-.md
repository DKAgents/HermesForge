---
type: insight
date: 2026-08-22
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
# Pivot Stop Placement vs. 3:1 Reward/Risk: When Intraday Rules Conflict

## Discovery Summary

EN071 mandates a protective sell stop below the current day's low (or today's open for late entries), but RG035 requires stops to be sized so that maximum loss never exceeds 5% of account ($5,000 on $100k). If the current day's low is far from the entry triggered by the buy stop above the previous day's high, the technically valid stop (EN071) may force a position size so small it violates the 3:1 reward/risk threshold, or conversely a position so large it breaches the 5% loss limit. C245 further warns that in fast markets the actual fill on the buy stop may exceed the stop price, widening the risk beyond the technically defined level and further straining the reward/risk ratio.

## Trading Implication

Before entering any pivot-point buy signal (EN071), calculate the distance from the expected entry (above previous day's high) to the required technical stop (below current day's low or today's open); if this distance — adjusted for slippage per C245 — produces a position size that either breaches the 5% loss cap (RG035) or fails a 3:1 reward/risk test, skip the trade entirely regardless of signal validity.

## Supporting Notes

- [[C245-stop-order]]
- [[RG035-combining-technical-factors-with-money-management-for-stop-p]]
- [[EN071-pivot-point-buy-signal-rules]]

## Connection Type

**resolves_conflict** — Actionability score: 4/5
