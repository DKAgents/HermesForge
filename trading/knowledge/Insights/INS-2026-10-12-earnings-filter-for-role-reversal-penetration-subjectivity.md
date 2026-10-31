---
type: insight
date: 2026-10-12
actionability: 4
connection_type: creates_filter
domains: [concepts, edge-conditions, event-risk, trading-rules]
sources: ["E005-subjectivity-in-defining-significant-penetration", "C065-previous-support-as-future-resistance-in-downtrend"]
seed_id: lesson-a-c8b706
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# Earnings filter for role-reversal penetration subjectivity

## Discovery Summary

C065 describes previous support becoming resistance in downtrends, but E005 warns that defining a 'significant penetration' of such levels is inherently subjective. The seed insight adds a mandatory earnings calendar binary filter to this role-reversal entry: if earnings are within 7 days, the trade is invalid. This removes a major source of false penetrations caused by scheduled event gaps rather than genuine technical role reversal.

## Trading Implication

Before entering a previous-support-as-resistance trade, verify the earnings date; if it falls within 7 days, skip the setup entirely.

## Supporting Notes

- [[E005-subjectivity-in-defining-significant-penetration]]
- [[C065-previous-support-as-future-resistance-in-downtrend]]

## Connection Type

**creates_filter** — Actionability score: 4/5
