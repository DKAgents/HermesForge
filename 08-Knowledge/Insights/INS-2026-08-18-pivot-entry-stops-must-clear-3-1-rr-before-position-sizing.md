---
type: insight
date: 2026-08-18
actionability: 4
connection_type: resolves_conflict
domains: [concepts, risk-guidelines, rules]
sources: ["C245-stop-order", "RG035-combining-technical-factors-with-money-management-for-stop-p", "EN071-pivot-point-buy-signal-rules"]
seed_id: prior_swing_low_stop
tags: [insight, discovery, knowledge-evolution]
---

# Pivot Entry Stops Must Clear 3:1 RR Before Position Sizing

## Discovery Summary

EN071's pivot point buy signal rules specify stop placement at the current day's low (or today's open for the late-session entry), while RG035 requires stops to be placed at valid technical levels AND satisfy a maximum 5% risk on the total position. The conflict emerges when the pivot rule's mechanically-defined stop distance is too wide to achieve a 3:1 reward/risk ratio given the account's 10% commitment cap — the stop is technically valid per EN071 but financially oversized per RG035. C245 further complicates this by noting actual fill prices may exceed stop prices in fast markets, meaning the true risk could be larger than planned, further eroding the reward/risk ratio.

## Trading Implication

Before entering a pivot point buy signal, calculate whether the distance from entry (above prior high or current high) to the EN071-defined protective stop satisfies a 3:1 reward/risk ratio given RG035's 5% maximum risk cap; if the stop distance is too wide, skip the trade rather than widen the risk budget or move the stop to an arbitrary level.

## Supporting Notes

- [[C245-stop-order]]
- [[RG035-combining-technical-factors-with-money-management-for-stop-p]]
- [[EN071-pivot-point-buy-signal-rules]]

## Connection Type

**resolves_conflict** — Actionability score: 4/5
