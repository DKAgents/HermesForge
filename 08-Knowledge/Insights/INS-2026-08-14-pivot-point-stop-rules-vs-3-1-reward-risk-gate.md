---
type: insight
date: 2026-08-14
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
# Pivot Point Stop Rules vs 3:1 Reward/Risk Gate

## Discovery Summary

EN071 defines a specific intraday stop placement rule (protective sell stop below current day's low after buy stop is elected), while RG035 requires that any stop must also satisfy a money management constraint — maximum 5% risk on total account. The conflict emerges when the pivot point entry (buy stop above prior day's high) combined with the stop below current day's low produces a dollar risk that exceeds 5% of the $100,000 account, or when the resulting reward/risk ratio falls below 3:1. C245 clarifies that in fast markets, fill prices beyond the stop price can widen risk further, potentially violating RG035's constraint even when the technical level appears valid.

## Trading Implication

Before placing the EN071 pivot point buy stop, calculate the distance from the intended entry (prior day's high) to the protective stop (current day's low) in dollar terms; if that distance exceeds 5% of account equity or fails a 3:1 reward/risk test against a defined target, reduce position size per RG035 or skip the trade entirely.

## Supporting Notes

- [[C245-stop-order]]
- [[RG035-combining-technical-factors-with-money-management-for-stop-p]]
- [[EN071-pivot-point-buy-signal-rules]]

## Connection Type

**resolves_conflict** — Actionability score: 4/5
