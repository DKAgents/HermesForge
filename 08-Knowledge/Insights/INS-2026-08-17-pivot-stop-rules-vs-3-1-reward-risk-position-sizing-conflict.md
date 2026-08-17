---
type: insight
date: 2026-08-17
actionability: 4
connection_type: resolves_conflict
domains: [concepts, risk-guidelines, rules]
sources: ["C245-stop-order", "RG035-combining-technical-factors-with-money-management-for-stop-p", "EN071-pivot-point-buy-signal-rules"]
seed_id: prior_swing_low_stop
tags: [insight, discovery, knowledge-evolution]
---

# Pivot Stop Rules vs 3:1 Reward/Risk: Position Sizing Conflict

## Discovery Summary

EN071 mandates specific intraday stop placements (below current day's low or today's open) that are time-and-price-driven, while RG035 requires stops be placed at valid technical levels sized to a 5% max risk on total account. The conflict emerges when the pivot point buy stop triggers late in the day (35-min rule), placing the protective stop under today's open — a potentially wide gap that may consume the full 5% risk allowance without offering a 3:1 reward. C245 further warns that fast-market fills can push actual execution beyond the stop price, compressing the reward/risk ratio even further on these mechanically-placed stops.

## Trading Implication

Before entering a pivot point buy signal (EN071), calculate the distance between the buy stop trigger price and the required protective stop, then verify this distance satisfies both the 5% max-risk rule from RG035 and allows a 3:1 reward target; skip the trade or reduce position size if either condition fails.

## Supporting Notes

- [[C245-stop-order]]
- [[RG035-combining-technical-factors-with-money-management-for-stop-p]]
- [[EN071-pivot-point-buy-signal-rules]]

## Connection Type

**resolves_conflict** — Actionability score: 4/5
