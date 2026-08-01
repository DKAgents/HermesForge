---
type: insight
date: 2026-08-01
actionability: 4
connection_type: creates_filter
domains: [indicators, patterns, rules]
sources: ["N013-volume-as-a-filter-for-false-breakouts", "R052-filters-for-confirming-breakouts", "N028-bull-trap-false-upside-breakout"]
seed_id: breakout_volume_risk
tags: [insight, discovery, knowledge-evolution]
---

# Volume-Confirmed Breakout Filter with Stop Placement Logic

## Discovery Summary

N013, R052, and N028 collectively build a multi-layered breakout validation system. R052 provides structural filters (close beyond resistance, percentage criteria, two-day rule, Friday close) while N013 and N028 add volume as the confirmatory layer. The non-obvious connection is that these filters can be sequenced: first apply R052's price-based filters to qualify a breakout, then use N013/N028's volume signature (heavy volume on breakout, light volume on any retest decline) to confirm or deny. A bull trap per N028 fails both tests — light volume on the initial move and heavy volume on the reversal — giving a trader two distinct exit triggers rather than one ambiguous signal.

## Trading Implication

A trader should require both a closing price filter (R052: close beyond resistance, ideally two consecutive days or a Friday close) AND volume confirmation (N013: heavy volume on breakout) before entering; if a breakout clears the price filter but shows light volume, treat it as a potential bull trap per N028 and place a stop just below the breakout level, exiting immediately if subsequent decline occurs on heavy volume.

## Supporting Notes

- [[N013-volume-as-a-filter-for-false-breakouts]]
- [[R052-filters-for-confirming-breakouts]]
- [[N028-bull-trap-false-upside-breakout]]

## Connection Type

**creates_filter** — Actionability score: 4/5
