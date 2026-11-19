---
type: insight
date: 2026-11-18
actionability: 4
connection_type: creates_filter
domains: [earnings calendar, risk guidelines, role-reversal, support/resistance, trading rules, trendlines]
sources: ["E005-subjectivity-in-defining-significant-penetration", "C065-previous-support-as-future-resistance-in-downtrend", "R029-speed-resistance-lines-role-reversal"]
seed_id: lesson-a-c8b706
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# Earnings Calendar as Mandatory Filter for Role-Reversal Entries

## Discovery Summary

E005-subjectivity-in-defining-significant-penetration exposes a key weakness in role-reversal signals such as those in C065-previous-support-as-future-resistance-in-downtrend and R029-speed-resistance-lines-role-reversal: the same price move can be read as either a valid breakout or a false penetration. Adding a pre-trade earnings calendar check directly filters out high-catalyst periods where support/resistance or speedline breaks are more likely to be earnings-driven noise rather than genuine role-reversal signals. The seed refines the role-reversal entry criteria by making this check mandatory and binary, addressing the subjectivity flagged in E005.

## Trading Implication

Before entering any trade based on violated support becoming resistance or a broken speedline, check the earnings calendar; if earnings are within 7 days, skip the trade and wait for post-earnings confirmation.

## Supporting Notes

- [[E005-subjectivity-in-defining-significant-penetration]]
- [[C065-previous-support-as-future-resistance-in-downtrend]]
- [[R029-speed-resistance-lines-role-reversal]]

## Connection Type

**creates_filter** — Actionability score: 4/5
