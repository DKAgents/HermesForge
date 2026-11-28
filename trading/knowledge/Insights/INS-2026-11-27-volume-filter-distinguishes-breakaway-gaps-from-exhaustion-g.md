---
type: insight
date: 2026-11-27
actionability: 4
connection_type: creates_filter
domains: [concepts, patterns, rules]
sources: ["N150-price-gaps-types", "R082-breakouts-must-be-accompanied-by-heavy-volume", "C328-gaps"]
seed_id: gap_continuation_volume
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# Volume filter distinguishes breakaway gaps from exhaustion gaps

## Discovery Summary

N150-price-gaps-types says breakaway gaps signal the start of a new trend, while R082-breakouts-must-be-accompanied-by-heavy-volume requires heavy volume to validate any real breakout. Applying R082 to gaps means a breakaway gap should only be traded as a trend-starting signal if it is accompanied by a volume surge. A gap without such volume confirmation is more likely a common gap or an exhaustion gap, not a valid breakout.

## Trading Implication

Do not chase a gap until volume confirms it; enter in the gap direction only on high-volume breakaway gaps, and treat low-volume gaps or gaps late in a trend as exhaustion/fade candidates.

## Supporting Notes

- [[N150-price-gaps-types]]
- [[R082-breakouts-must-be-accompanied-by-heavy-volume]]
- [[C328-gaps]]

## Connection Type

**creates_filter** — Actionability score: 4/5
