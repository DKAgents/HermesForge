---
type: insight
date: 2026-10-28
actionability: 4
connection_type: creates_filter
domains: [concepts, trading rules]
sources: ["C050-secondary-trend-retracement-range", "EN068-4060-retracement-zones-for-timing-entries"]
seed_id: swing_low_entry_filter
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# Fibonacci Retracement Zones for Uptrend Pullback Entries

## Discovery Summary

C050 defines the secondary trend retracement range (typically one-third to two-thirds of the prior move). EN068-4060 converts this range into Fibonacci retracement zones for timing entries, with Murphy's ideal entry point near the 50% retracement. The rule operationalizes the concept by filtering entries to pullbacks that reach the 38.2%-61.8% zone, where the secondary reaction likely ends and the primary trend resumes.

## Trading Implication

In an uptrend, only enter on pullbacks that reach the Fibonacci 38.2%-61.8% retracement zone, preferably at the 50% level, with a stop below the 61.8% level or prior swing low.

## Supporting Notes

- [[C050-secondary-trend-retracement-range]]
- [[EN068-4060-retracement-zones-for-timing-entries]]

## Connection Type

**creates_filter** — Actionability score: 4/5

## Related Notes
- [[C050-secondary-trend-retracement-range|Secondary Trend Retracement Range]]
- [[INS-2026-10-15-fibonacci-40-60-retracement-zone-for-pullback-entries|Fibonacci 40-60% retracement zone for pullback entries]]
