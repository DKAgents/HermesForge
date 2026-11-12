---
type: insight
date: 2026-11-11
actionability: 4
connection_type: adds_condition
domains: [concepts, edge-conditions, rules, trading-rules]
sources: ["E005-subjectivity-in-defining-significant-penetration", "C065-previous-support-as-future-resistance-in-downtrend", "R029-speed-resistance-lines-role-reversal"]
seed_id: lesson-a-c8b706
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# Earnings filter for subjective role-reversal entries

## Discovery Summary

E005-subjectivity-in-defining-significant-penetration explicitly acknowledges that no universal 'significant' threshold exists for support/resistance role reversal (Murphy p.83). C065-previous-support-as-future-resistance-in-downtrend and R029-speed-resistance-lines-role-reversal both depend on that same subjective break before price can be expected to reverse roles. The seed resolves this edge-case weakness by adding a mandatory pre-trade earnings calendar check as a binary filter, blocking role-reversal entries when earnings are within 7 days.

## Trading Implication

Before entering any trade based on a support-turned-resistance or broken speedline role-reversal signal, check the earnings calendar and skip the trade if earnings are within 7 days.

## Supporting Notes

- [[E005-subjectivity-in-defining-significant-penetration]]
- [[C065-previous-support-as-future-resistance-in-downtrend]]
- [[R029-speed-resistance-lines-role-reversal]]

## Connection Type

**adds_condition** — Actionability score: 4/5
