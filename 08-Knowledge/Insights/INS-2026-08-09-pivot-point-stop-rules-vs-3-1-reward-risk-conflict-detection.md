---
type: insight
date: 2026-08-09
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
# Pivot Point Stop Rules vs. 3:1 Reward/Risk Conflict Detection

## Discovery Summary

EN071 specifies that protective sell stops are placed below the current day's low after a pivot point buy signal is elected, but RG035 requires stops to satisfy both technical levels AND money management constraints (max 5% risk on total account). If today's low is far from the buy stop trigger (e.g., a wide-range day), the technically mandated stop under today's low may exceed the 5% risk threshold, creating a direct conflict. C245 notes that fill prices may be beyond stop prices in fast markets, further eroding the reward/risk ratio below 3:1 even when the stop placement appears technically valid.

## Trading Implication

Before placing the pivot point buy stop per EN071, calculate the distance from entry to the protective stop below today's low — if this distance violates the 5% maximum risk rule from RG035, reduce position size accordingly or skip the trade if the resulting position size is too small to be meaningful.

## Supporting Notes

- [[C245-stop-order]]
- [[RG035-combining-technical-factors-with-money-management-for-stop-p]]
- [[EN071-pivot-point-buy-signal-rules]]

## Connection Type

**resolves_conflict** — Actionability score: 4/5

## Related Notes
- [[RG020-protective-sell-stops-on-point-and-figure-charts|Protective Sell Stops on Point and Figure Charts]]
- [[EN071-pivot-point-buy-signal-rules|Pivot Point Buy Signal Rules]]
