---
type: insight
date: 2026-08-07
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
# Pivot Stop Rules vs 3:1 Reward/Risk: Position Size Conflict

## Discovery Summary

EN071 defines precise intraday stop placement mechanics (below current day's low or today's open), while RG035 requires stops to satisfy both technical levels AND a maximum 5% portfolio risk per trade. The conflict emerges when the pivot point rules dictate a technically valid but wide stop — e.g., stop under today's open when entry is above the previous day's high — which may force position size reduction to stay within 5% risk, potentially shrinking reward potential below the implied 3:1 threshold. C245 notes that fills may be beyond stop price in fast markets, adding slippage risk that further erodes the reward/risk ratio calculated at entry.

## Trading Implication

Before entering on EN071's 35-minute-close buy stop signal, calculate the dollar distance to the required protective stop and verify position sizing under RG035's 5% rule still permits a 3:1 reward/risk target; if not, skip the trade rather than widen the stop or accept an undersized reward.

## Supporting Notes

- [[C245-stop-order]]
- [[RG035-combining-technical-factors-with-money-management-for-stop-p]]
- [[EN071-pivot-point-buy-signal-rules]]

## Connection Type

**resolves_conflict** — Actionability score: 4/5
