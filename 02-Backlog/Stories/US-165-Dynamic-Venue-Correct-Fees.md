---
type: user-story
epic: EPIC-014
priority: P0
status: backlog
created: 2026-10-31
tags: [pnl-integrity, cost-model, g3]
---

# US-165 — Replace static venue costs with dynamic venue-correct fees

## Problem

`scripts/gauntlet/cost_adjuster.py` hardcodes `VENUE_COSTS = {"stock": 2.0, "crypto": 12.0}`. It is static, fee-tier-agnostic, referral-blind, and never reflects Hyperliquid's actual/current fee schedule. The `stock = 2 bps` assumption is zero-commission (flattering for most brokers). Principal confirmed: we are NOT using historical/actual Hyperliquid fees today — the 12 bps traces to PROP-001's static base-tier assumption.

## Fix

Replace the static constant with a dynamic, venue-correct fee source:
- Fetch Hyperliquid's current base-tier fee schedule at runtime from the info endpoint (`{"type": "userFees", "user": <addr>}` or the meta/base-tier equivalent), with a cache + TTL so it does not hit the API per-trade.
- Fail-closed: on API error/timeout, fall back to a conservative default (never a more favorable one).
- Add a realistic non-zero-commission stock cost (document the broker/taker assumption).
- Keep the documented `fee_tier_assumed`/fallback visible so the mode is auditable.

## Acceptance

- Fee model is dynamic (updates when Hyperliquid changes its base tier) with a fail-closed static fallback.
- Stock is no longer zero-commission.
- Downstream `compute_cost_drag` / `_paper_r` / `_adversarial_cost_drag` consume the dynamic source.
- Documented tier assumption + fallback behavior; unit-test the fail-closed path.