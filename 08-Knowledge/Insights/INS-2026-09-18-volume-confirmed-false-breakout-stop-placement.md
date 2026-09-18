---
type: insight
date: 2026-09-18
actionability: 4
connection_type: reveals_sequence
domains: [indicators, patterns, rules]
sources: ["N013-volume-as-a-filter-for-false-breakouts", "R052-filters-for-confirming-breakouts", "N028-bull-trap-false-upside-breakout"]
seed_id: breakout_volume_risk
tags: [insight, discovery, knowledge-evolution]
---

# Volume-Confirmed False Breakout Stop Placement

## Discovery Summary

Combining the volume filter from N013 (light volume breakout followed by heavy volume decline) with the breakout confirmation rules in R052 (e.g., close beyond resistance, volume check) provides a clear sequence to identify a bull trap (N028). Once the false breakout is confirmed, the trader can place stops below the breakout level or exit immediately on the heavy volume decline.

## Trading Implication

After a breakout on light volume, if a subsequent decline occurs on heavy volume, immediately exit or tighten stops below the breakout level to capture the reversal.

## Supporting Notes

- [[N013-volume-as-a-filter-for-false-breakouts]]
- [[R052-filters-for-confirming-breakouts]]
- [[N028-bull-trap-false-upside-breakout]]

## Connection Type

**reveals_sequence** — Actionability score: 4/5
