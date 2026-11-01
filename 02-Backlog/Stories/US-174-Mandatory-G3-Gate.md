---
type: user-story
epic: EPIC-014
priority: P0
status: backlog
created: 2026-11-01
tags: [governance, fill-realism, promotion-gate]
---

# US-174 — Make G3 fill-realism a mandatory promotion gate

## Problem

Strategies were promoted to LIVE/WATCH on frictionless/optimistic-fill edges (the root cause of the STR-Q and 16-chart-pattern hidden losers). There is no enforced gate requiring an edge to survive realistic/pessimistic fills before promotion.

## Fix

Make G3 execution realism (pessimistic/realistic fill mode via `execution_sim.py` / hostile fills) a MANDATORY gate: a strategy cannot be promoted to LIVE/WATCH unless its edge is positive under realistic fills. Enforce this in the promotion path (`validate_strategy.py` / promotion logic), not as a manual convention.

## Acceptance

- The promotion path checks and rejects any strategy whose realistic-fill edge is ≤ 0 (or flags it "no claimable edge").
- Documented in ADR or the gauntlet spec as a binding rule.