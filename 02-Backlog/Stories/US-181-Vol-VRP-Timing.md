---
type: user-story
epic: EPIC-016
priority: P1
status: backlog
created: 2026-11-01
tags: [alpha, volatility, vrp]
---

# US-181 — Vol / variance-risk-premium with vol-of-vol timing

## Problem

The negative VRP is the most robustly documented premium, but unconditional short-vol is tail-risky ("pennies in front of a steamroller"). Conditioning on vol-of-vol (e.g. morning VVIX) yields Sharpe 0.76–3.24 — roughly 2–3× the unconditional short-vol Sharpe — and the signal decays by midday, evidencing a genuine under-reaction.

## Fix

Design a short-vol / short-VRP strategy gated on vol-of-vol (and regime), with tail-risk hedges in the constitution and margin accounted for (short-straddle margin ≥ premium + ~20% underlying).

## Acceptance

- A vol-timing entry rule (vol-of-vol condition) + risk constitution with tail hedges.
- A backtest showing the timed short-vol edge dominates unconditional short-vol, surviving the G3 gate.