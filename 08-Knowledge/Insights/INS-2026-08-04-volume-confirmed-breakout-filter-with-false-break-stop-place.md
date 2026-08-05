---
type: insight
date: 2026-08-04
actionability: 4
connection_type: creates_filter
domains: [indicators, patterns, rules]
sources: ["N013-volume-as-a-filter-for-false-breakouts", "R052-filters-for-confirming-breakouts", "N028-bull-trap-false-upside-breakout"]
seed_id: breakout_volume_risk
tags: [insight, discovery, knowledge-evolution]
topic: knowledge
confidence: high
has_quotes: false
source: unknown
---
# Volume-Confirmed Breakout Filter With False-Break Stop Placement

## Discovery Summary

N013 and N028 both establish that light-volume breakouts followed by heavy-volume declines signal bull traps, while R052 provides a multi-criteria confirmation framework (close-beyond, percentage filter, two-day rule, Friday close, volume). The non-obvious connection is that these filters from R052 can be sequenced specifically to gate against the bull-trap scenario described in N028: first require a closing breakout (not intraday), then confirm volume is heavy on the breakout day per N013, and only then commit. If volume is light on the breakout, R052's two-day penetration rule provides a secondary wait-and-see gate before entry. Together, the three notes create a tiered decision tree rather than isolated checks.

## Trading Implication

A trader should require simultaneously: (1) a closing price above the prior resistance peak, (2) above-average volume on the breakout candle, and (3) ideally a second consecutive closing day above the peak before entering long — placing a stop just below the breakout level so that a subsequent heavy-volume reversal (the bull-trap signal from N028) triggers an immediate exit.

## Supporting Notes

- [[N013-volume-as-a-filter-for-false-breakouts]]
- [[R052-filters-for-confirming-breakouts]]
- [[N028-bull-trap-false-upside-breakout]]

## Connection Type

**creates_filter** — Actionability score: 4/5
