---
type: user-story
epic: EPIC-017
priority: P1
status: backlog
created: 2026-11-02
owner: researcher
tags: [hypothesis, universe, hyperliquid]
---

# US-203 — Universe filter: Hyperliquid-only instruments

## Description
Only instruments tradeable on Hyperliquid (perps/spot) run the Gauntlet. Equities, FX, gold, and single-stock signals are parked in a separate backlog, not run through the Gauntlet.

## Acceptance Criteria
- Intake rejects any seed whose instruments are not HL-tradeable.
- A separate "parked" backlog holds equities/FX/gold/single-stock ideas.
- Verified: an equity seed routes to the parked backlog, not the Gauntlet.

## Owner / RACI
- Owner (A): researcher · Responsible (R): coder · Consulted (C): product-owner · Informed (I): orchestrator