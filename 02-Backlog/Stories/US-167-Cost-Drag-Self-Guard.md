---
type: user-story
epic: EPIC-014
priority: P2
status: backlog
created: 2026-10-31
tags: [pnl-integrity, tech-debt]
---

# US-167 — `_adversarial_cost_drag` self-guard

## Problem

`_adversarial_cost_drag` divides by `entry_price` unconditionally. Every call site guards `entry_price <= 0` first, so it is not a live bug, but the function itself has no self-guard (latent foot-gun — risk-guardian round-3 finding).

## Fix

Add an internal guard: `entry_price <= 0` (or `stop_price <= 0`) returns a conservative sentinel (e.g. `inf`) inside the function itself, so no future call site can trigger a ZeroDivisionError.

## Acceptance

- `_adversarial_cost_drag(0, x)` and `_adversarial_cost_drag(-1, x)` return the sentinel, no exception.
- Unit test covers the zero/negative paths.