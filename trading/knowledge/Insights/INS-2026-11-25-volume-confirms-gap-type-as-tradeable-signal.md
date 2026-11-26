---
type: insight
date: 2026-11-25
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
# Volume Confirms Gap Type as Tradeable Signal

## Discovery Summary

Breakaway and runaway gaps represent breakout points where price leaves a prior range. According to R082-breakouts-must-be-accompanied-by-heavy-volume, all breakouts require heavy volume to be valid. Therefore, a gap without high volume is more likely a common gap that will be filled, while a high-volume breakaway gap signals a new trend (chase) and a high-volume exhaustion gap signals a potential reversal (fade).

## Trading Implication

Before acting on any gap, check the volume on the gap bar. Only trade gaps with volume expansion; treat low-volume gaps as common gaps to fade.

## Supporting Notes

- [[N150-price-gaps-types]]
- [[R082-breakouts-must-be-accompanied-by-heavy-volume]]
- [[C328-gaps]]

## Connection Type

**adds_condition** — Actionability score: 4/5
