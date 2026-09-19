---
type: insight
date: 2026-09-19
actionability: 4
connection_type: creates_filter
domains: [concepts, risk-guidelines, rules]
sources: ["C245-stop-order", "RG035-combining-technical-factors-with-money-management-for-stop-p", "EN071-pivot-point-buy-signal-rules"]
seed_id: prior_swing_low_stop
tags: [insight, discovery, knowledge-evolution]
---

# Pivot stop conflict with money management risk limits

## Discovery Summary

The pivot point buy signal rule (EN071) mandates a protective stop below the current day's low (or under today's open), while money management (RG035) requires stops to be at valid technical levels and caps risk at 5% of account value. The distance from entry to that technical stop determines the risk per share, which then limits position size. If that stop is too wide, the resulting position size may be too small to justify the trade, or the risk percentage may exceed 5%, conflicting with a 3:1 reward/risk requirement (implied by common practice).

## Trading Implication

Before executing a pivot point breakout, calculate the dollar risk from the specified stop, then compute the maximum position size using the 5% rule. If the implied position size is below a minimum threshold or the reward/risk ratio fails, skip the trade.

## Supporting Notes

- [[C245-stop-order]]
- [[RG035-combining-technical-factors-with-money-management-for-stop-p]]
- [[EN071-pivot-point-buy-signal-rules]]

## Connection Type

**creates_filter** — Actionability score: 4/5
