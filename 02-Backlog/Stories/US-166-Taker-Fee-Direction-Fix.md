---
type: user-story
epic: EPIC-014
priority: P1
status: backlog
created: 2026-10-31
tags: [pnl-integrity, cost-model]
---

# US-166 — Fix `_apply_taker_fee` direction-blindness

## Problem

`_apply_taker_fee(price, is_entry)` (hostile_fills*.py) has no `direction` argument, so the round-trip taker fee is never actually charged in the adverse direction for either long or short. Risk-guardian round-1 residual: "the round-trip fee is never actually charged in either direction — the hostile model overstates both longs and shorts by the same 20 bps."

## Fix

Thread `direction` (long/short) through `_apply_taker_fee` and compute the adverse-side fee correctly so the full round trip is charged identically for longs and shorts.

## Acceptance

- A long round trip and a short round trip charge the same total taker fee.
- Unit test demonstrates the fee is now levied (no direction-blind zero).
- Consumed by the shared accounting module (US-164) once consolidated.