---
type: insight
date: 2026-09-20
actionability: 4
connection_type: resolves_conflict
domains: [concepts, risk-guidelines, rules]
sources: ["RG023-pf-trailing-stop-adjustment", "C245-stop-order", "EN071-pivot-point-buy-signal-rules"]
seed_id: system_exit_design
tags: [insight, discovery, knowledge-evolution]
topic: knowledge
confidence: high
has_quotes: false
source: Murphy - Technical Analysis of the Financial Markets
---
# Exits Over Entries: Stop Placement Mirrors Murphy's Exit Priority

## Discovery Summary

Murphy's emphasis on exits over entries is operationalized by stop placement rules across these notes. RG023-pf-trailing-stop-adjustment shows trailing stops based on P&F columns, while EN071-pivot-point-buy-signal-rules places protective stops under recent lows, and C245-stop-order defines stop mechanics. The non-obvious connection is that entry signals (pivot buy, P&F buy) are validated not by the entry itself but by the immediate stop level, which defines the risk/reward. Both EN071 and RG023 place stops at structurally significant levels (recent low, latest o column), proving that exit planning is integrated into the entry decision, aligning with Murphy's view that successful trading depends on managing exits, not finding perfect entries.

## Trading Implication

When taking any buy signal (pivot or P&F), immediately identify the protective stop using the specific rule (below current day's low or latest o column) and confirm that the potential reward is at least three times the stop distance; if not, skip the trade. This places exit management at the forefront of trade selection, as Murphy advises.

## Supporting Notes

- [[RG023-pf-trailing-stop-adjustment]]
- [[C245-stop-order]]
- [[EN071-pivot-point-buy-signal-rules]]

## Connection Type

**resolves_conflict** — Actionability score: 4/5

## Related Notes
- [[INS-2026-09-16-volume-confirmed-breakout-stop-placement-rule|Volume-Confirmed Breakout Stop Placement Rule]]
