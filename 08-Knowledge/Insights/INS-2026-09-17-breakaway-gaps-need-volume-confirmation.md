---
type: insight
date: 2026-09-17
actionability: 4
connection_type: adds_condition
domains: [concepts, patterns, rules]
sources: ["N150-price-gaps-types", "R082-breakouts-must-be-accompanied-by-heavy-volume", "C328-gaps"]
seed_id: gap_continuation_volume
tags: [insight, discovery, knowledge-evolution]
topic: knowledge
confidence: high
has_quotes: false
source: unknown
---
# Breakaway gaps need volume confirmation

## Discovery Summary

The 'Price Gaps Types' note explains breakaway gaps signal new trends, while 'Breakouts Must Be Accompanied by Heavy Volume' requires heavy volume for valid breakouts. Since breakaway gaps are a form of breakout, applying the volume condition filters out false gaps.

## Trading Implication

Trade breakaway gaps only when accompanied by above-average volume; ignore low-volume breakaway gaps as likely false signals.

## Supporting Notes

- [[N150-price-gaps-types]]
- [[R082-breakouts-must-be-accompanied-by-heavy-volume]]
- [[C328-gaps]]

## Connection Type

**adds_condition** — Actionability score: 4/5
