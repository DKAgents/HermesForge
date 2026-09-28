---
type: insight
date: 2026-09-28
actionability: 4
connection_type: confirms_risk_rule
domains: [indicators, patterns, rules]
sources: ["N013-volume-as-a-filter-for-false-breakouts", "R052-filters-for-confirming-breakouts", "N028-bull-trap-false-upside-breakout"]
seed_id: breakout_volume_risk
tags: [insight, discovery, knowledge-evolution]
---

# Volume filter stops to avoid bull traps

## Discovery Summary

N013 volume filter identifies false breakouts, which are precisely the bull traps described in N028. R052's confirmation filters align with N013, so combining them yields a rule: only trade breakouts with above-threshold volume; on low volume, place stops just below the breakout level to exit potential bull traps.

## Trading Implication

When a breakout occurs with low volume, treat it as a possible bull trap and place a stop loss immediately below the breakout point to limit losses.

## Supporting Notes

- [[N013-volume-as-a-filter-for-false-breakouts]]
- [[R052-filters-for-confirming-breakouts]]
- [[N028-bull-trap-false-upside-breakout]]

## Connection Type

**confirms_risk_rule** — Actionability score: 4/5
