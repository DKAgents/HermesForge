---
type: insight
date: 2026-10-29
actionability: 4
connection_type: adds_condition
domains: [concepts, risk guidelines, rules]
sources: ["C366-secondary-trends", "EN041-oscillator-entry-strategy-in-trending-markets"]
seed_id: oscillator_trending_market
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# Oscillator entries in strong trends avoid counter-trend secondary moves

## Discovery Summary

C366-secondary-trends defines counter-primary corrective moves, while EN041-oscillator-entry-strategy-in-trending-markets uses oscillators to time entries in trending conditions. The edge condition that oscillators 'lie' in strong trends—staying overbought/oversold—makes counter-trend oscillator signals unreliable during secondary corrections. Thus EN041 should only be applied when the oscillator signal aligns with the primary trend; signals against it during a secondary trend are false and conflict with risk rules on counter-trend trades.

## Trading Implication

Filter EN041 oscillator entries to those in the direction of the primary trend; ignore or apply stricter counter-trend risk rules to any oscillator signal that fires against the primary trend, especially during secondary corrections.

## Supporting Notes

- [[C366-secondary-trends]]
- [[EN041-oscillator-entry-strategy-in-trending-markets]]

## Connection Type

**adds_condition** — Actionability score: 4/5
