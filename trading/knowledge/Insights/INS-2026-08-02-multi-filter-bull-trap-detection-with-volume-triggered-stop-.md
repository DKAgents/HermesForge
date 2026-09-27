---
type: insight
date: 2026-08-02
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
# Multi-Filter Bull Trap Detection with Volume-Triggered Stop Placement

## Discovery Summary

N013 and N028 together establish that a false upside breakout (bull trap) can be identified by two sequential volume signals: light volume on the initial breakout followed by heavy volume on the subsequent decline. R052 adds structural confirmation filters (close-beyond, 1-3% penetration, two-day rule, Friday close) that must precede volume analysis. The non-obvious synthesis is that these filters operate in sequence: first apply R052's price-based filters to assess breakout validity, then apply N013/N028's volume test to confirm or deny — and critically, the heavy-volume decline following a light-volume breakout is the actionable trigger for stop placement or short entry, not the breakout itself.

## Trading Implication

A trader should wait for a suspected breakout to fail the R052 structural filters (no confirmed close, sub-1% penetration, or single-day only), then watch for a heavy-volume decline as the entry trigger for a short trade or the signal to exit longs — placing stops just above the failed breakout high.

## Supporting Notes

- [[N013-volume-as-a-filter-for-false-breakouts]]
- [[R052-filters-for-confirming-breakouts]]
- [[N028-bull-trap-false-upside-breakout]]

## Connection Type

**creates_filter** — Actionability score: 4/5

## Related
- [[RG003-protective-stop-placement-relative-to-round-numbers]] — Avoid obvious round numbers when placing volume-triggered stops

- [[R082-breakouts-must-be-accompanied-by-heavy-volume]] — See R082-breakouts-must-be-accompanied-by-heavy-volume for the volume validation rule that bull traps violate

- [[RG035-combining-technical-factors-with-money-management-for-stop-p]] — Ensure volume-triggered stops align with technical levels per RG035
