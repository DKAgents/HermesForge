---
type: insight
date: 2026-11-02
actionability: 4
connection_type: adds_condition
domains: [concepts, patterns, rules]
sources: ["N150-price-gaps-types", "R082-breakouts-must-be-accompanied-by-heavy-volume", "C328-gaps"]
seed_id: gap_continuation_volume
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# Volume Confirms Breakaway Gaps, Filters Common Gaps

## Discovery Summary

The 'Price Gaps Types' note identifies breakaway gaps as trend-start signals, but the 'Breakouts Must Be Accompanied by Heavy Volume' rule implies that a gap alone is not sufficient—if the gap is a true breakout, volume must surge. Therefore, volume acts as a discriminator: a breakaway gap on high volume is valid and chaseable, while a gap on light volume is likely a common gap or exhaustion, not a breakout.

## Trading Implication

When a gap occurs at a consolidation boundary, check volume before acting: if volume is significantly above average, treat it as a breakout and consider entering; if volume is low, do not chase—it is likely a common gap that will fill.

## Supporting Notes

- [[N150-price-gaps-types]]
- [[R082-breakouts-must-be-accompanied-by-heavy-volume]]
- [[C328-gaps]]

## Connection Type

**adds_condition** — Actionability score: 4/5
