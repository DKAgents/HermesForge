---
type: insight
date: 2026-11-05
actionability: 3
connection_type: creates_filter
domains: [indicators, patterns, rules]
sources: ["N043-flag-and-pennant-summary-characteristics", "R082-breakouts-must-be-accompanied-by-heavy-volume", "N013-volume-as-a-filter-for-false-breakouts"]
seed_id: vol_diverge_stop
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# Volume divergence in flag/pennant breakouts: tighten stops

## Discovery Summary

N043 defines the flag/pennant volume sequence: heavy volume on the flagpole, very light volume during the 1-3 week pause, then a heavy-volume burst on resumption. R082 and N013 add that breakouts are only valid with heavy volume, while a light-volume breakout is suspect and a subsequent heavy-volume decline confirms a false breakout. Together they create a volume-based filter: any divergence from the expected sequence—especially heavy volume during the pause or a light-volume breakout—warns that the continuation pattern is failing and stops should be tightened.

## Trading Implication

When trading a flag/pennant, watch volume during the pause and at the breakout; if pause volume is not light or the breakout is not heavy, tighten stops below the pattern/flagpole and exit on a heavy-volume decline.

## Supporting Notes

- [[N043-flag-and-pennant-summary-characteristics]]
- [[R082-breakouts-must-be-accompanied-by-heavy-volume]]
- [[N013-volume-as-a-filter-for-false-breakouts]]

## Connection Type

**creates_filter** — Actionability score: 3/5
