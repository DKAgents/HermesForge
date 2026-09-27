---
type: insight
date: 2026-08-05
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
# Stack Multiple Breakout Filters to Confirm and Place Stops

## Discovery Summary

N013 and N028 establish that light-volume upside breakouts followed by heavy-volume declines are the signature of a bull trap, while R052 provides a menu of five confirmation filters. The non-obvious connection is that volume analysis (N013/N028) should be treated as a mandatory sixth filter stacked on top of R052's price-based criteria — a breakout that passes the 1-3% penetration or two-day close rule but occurs on light volume should still be disqualified or treated with stop placement just below the breakout level. The heavy-volume decline signal from N028 then becomes the stop-trigger event, not just a post-hoc warning.

## Trading Implication

A trader should require BOTH a price-filter confirmation from R052 (e.g., two consecutive closes above resistance) AND above-average volume on the breakout day; if volume is light on the breakout, place a tight stop just below the breakout level so that any subsequent heavy-volume reversal automatically exits the position before the bull trap fully develops.

## Supporting Notes

- [[N013-volume-as-a-filter-for-false-breakouts]]
- [[R052-filters-for-confirming-breakouts]]
- [[N028-bull-trap-false-upside-breakout]]

## Connection Type

**creates_filter** — Actionability score: 4/5
