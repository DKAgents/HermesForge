---
type: insight
date: 2026-11-25
actionability: 4
connection_type: confirms_risk_rule
domains: [indicators, patterns, trading_rules]
sources: ["N013-volume-as-a-filter-for-false-breakouts", "R052-filters-for-confirming-breakouts", "N028-bull-trap-false-upside-breakout"]
seed_id: breakout_volume_risk
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# Volume Filter Confirms Breakout Stops

## Discovery Summary

N013 shows that valid upside breakouts need heavy volume, while light-volume breakouts are suspect and a subsequent heavy-volume decline signals a false breakout. R052 adds confirmation filters such as closes beyond resistance and volume checks. N028 describes the bull trap as a light-volume breakout followed by heavy-volume decline. Together, these notes confirm that a breakout lacking volume confirmation should trigger protective stops, with the heavy-volume decline validating the exit.

## Trading Implication

Traders should require volume confirmation on breakouts and place protective stops when volume is light; exit if a decline occurs on heavy volume, as the breakout is likely false.

## Supporting Notes

- [[N013-volume-as-a-filter-for-false-breakouts]]
- [[R052-filters-for-confirming-breakouts]]
- [[N028-bull-trap-false-upside-breakout]]

## Connection Type

**confirms_risk_rule** — Actionability score: 4/5
