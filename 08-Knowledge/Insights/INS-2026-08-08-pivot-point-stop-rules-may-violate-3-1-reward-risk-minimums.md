---
type: insight
date: 2026-08-08
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
# Pivot Point Stop Rules May Violate 3:1 Reward/Risk Minimums

## Discovery Summary

EN071 defines a mechanical intraday stop placement rule (below current day's low or below today's open) that is time-bound and context-specific, while RG035 requires stops to simultaneously satisfy both technical validity AND money management criteria including an implied reward/risk ratio. C245 warns that fills in fast markets may exceed stop prices. The conflict arises when the pivot point buy stop triggers late in the session (35-min rule) and the protective stop under today's open is too close or too far to yield a 3:1 reward/risk — the mechanical rule in EN071 gives no provision for skipping the trade when reward/risk is inadequate.

## Trading Implication

Before executing either pivot point entry variant in EN071, calculate the distance from entry to protective stop and verify the implied profit target meets at least 3:1 reward/risk; if not, skip the trade regardless of the mechanical signal being triggered.

## Supporting Notes

- [[C245-stop-order]]
- [[RG035-combining-technical-factors-with-money-management-for-stop-p]]
- [[EN071-pivot-point-buy-signal-rules]]

## Connection Type

**resolves_conflict** — Actionability score: 4/5

## Related Notes
- [[RG022-pf-stop-placement-rule|P&F Stop Placement Rule]]
- [[EN071-pivot-point-buy-signal-rules|Pivot Point Buy Signal Rules]]
