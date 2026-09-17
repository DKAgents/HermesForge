---
type: insight
date: 2026-09-17
actionability: 4
connection_type: confirms_risk_rule
domains: [indicators, patterns, risk_management, trading_rules]
sources: ["N013-volume-as-a-filter-for-false-breakouts", "R052-filters-for-confirming-breakouts", "N028-bull-trap-false-upside-breakout"]
seed_id: breakout_volume_risk
tags: [insight, discovery, knowledge-evolution]
---

# Confirming Breakouts and Placing Stops with Volume Confirmation

## Discovery Summary

The notes N028 and N013 independently describe the same negative volume pattern: a false upside breakout on light volume followed by a decline on heavy volume signals a bull trap. R052 provides additional confirmation filters (close beyond resistance, percentage penetration, two-day rule) but emphasizes volume as a reliability clue. The connection between these notes creates a clear sequence: first use R052's price filters to confirm a breakout has occurred, then check volume to validate its strength. If price breaks out on light volume and subsequently closes below the breakout level, the trader can treat it as a confirmed false breakout and immediately place a stop above the breakout high (or below a recent swing low) to capitalize on the reversal.

## Trading Implication

For long entries, require a closing breakout with confirming volume per R052 and N013; if the breakout occurs on light volume and price later closes back below the prior resistance (now support), place a short stop at the breakout high, anticipating a decline on heavy volume. For stop placement on any breakout, use the breakout level with a buffer—if price closes beyond that level on light volume, widen the stop or avoid the trade entirely.

## Supporting Notes

- [[N013-volume-as-a-filter-for-false-breakouts]]
- [[R052-filters-for-confirming-breakouts]]
- [[N028-bull-trap-false-upside-breakout]]

## Connection Type

**confirms_risk_rule** — Actionability score: 4/5
