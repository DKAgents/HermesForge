---
type: user-story
epic: EPIC-016
priority: P0
status: backlog
created: 2026-11-01
tags: [alpha, funding-rate, carry, crypto]
---

# US-179 — Funding/basis carry strategy (delta-neutral crypto)

## Problem

The retail TA/signal class has no raw alpha. The evidence-based replacement Tier-1 edge is **funding-rate / basis carry** (delta-neutral crypto): stable elevated funding compounds to 8–18%/yr after fees, and it persists because it is structurally short the crowd's leverage demand — not a price-mean-reversion bet that gets arbitraged away.

## Fix

Design + build a delta-neutral funding-rate carry strategy:
- Data: Hyperliquid funding rate history + current funding (per-hour), plus the basis/carry spread.
- Signal: gate entries on **sustained** multi-interval elevated funding (not single high readings); monitor rate-flip + basis-widening (the two documented killers).
- Construction: delta-neutral (long spot / short perp, or the equivalent), with the position size/capacity explicit.
- Validation: through the G3 gate (realistic fills), with the funding regime (bull/bear/neutral) partitioned.

## Acceptance

- A funding-carry signal with a documented sustained-funding entry rule + risk constitution.
- A backtest showing net edge after fees that survives the G3 gate and regime partitioning.