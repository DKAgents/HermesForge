---
type: insight
date: 2026-08-05
actionability: 4
connection_type: resolves_conflict
domains: [concepts, risk-guidelines, rules]
sources: ["C245-stop-order", "RG035-combining-technical-factors-with-money-management-for-stop-p", "EN071-pivot-point-buy-signal-rules"]
seed_id: prior_swing_low_stop
tags: [insight, discovery, knowledge-evolution]
---

# Pivot Stop Rules vs. 3:1 Reward/Risk: Hidden Conflict

## Discovery Summary

EN071 places the protective sell stop below the current day's low after a pivot breakout entry above the prior day's high — a mechanically defined stop. RG035 requires that stops satisfy both technical validity AND money management constraints (max 5% risk on total account). The conflict emerges when the distance from entry (above prior day's high) to the protective stop (below current day's low) is large relative to the profit target needed to achieve a 3:1 reward/risk ratio: a wide intraday range can make the trade technically valid per EN071 but mathematically invalid under RG035's position-sizing framework.

## Trading Implication

Before placing the EN071 pivot buy stop, calculate the entry-to-stop distance and verify a 3:1 reward target exists at a meaningful technical level; if the current day's range is too wide to allow 3:1 reward/risk within a $10,000 max position and 5% max risk, skip the trade entirely rather than widen the stop or reduce the target.

## Supporting Notes

- [[C245-stop-order]]
- [[RG035-combining-technical-factors-with-money-management-for-stop-p]]
- [[EN071-pivot-point-buy-signal-rules]]

## Connection Type

**resolves_conflict** — Actionability score: 4/5
