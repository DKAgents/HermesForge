---
type: user-story
epic: EPIC-017
priority: P1
status: backlog
created: 2026-11-02
owner: researcher
tags: [research, funding, carry, swing]
---

# US-212 — HYP-01 funding-extreme unwind at swing horizon

## Description
Run HYP-01 (funding-extreme unwind) at swing horizon 4–48h, using HL funding percentile + OKX funding spread + OI-delta quadrant. This is the *positioning-conditioned* replay of the funding signal (not the naked directional carry that structural analysis rejected).

## Acceptance Criteria
- Pre-registered construction: funding >95th %ile, OI-delta quadrant, cross-venue spread.
- Full Gauntlet run on the swing horizon.
- Honest verdict distinguishing funding edge from basis proxy.

## Owner / RACI
- Owner (A): researcher · Responsible (R): backtester · Consulted (C): risk-guardian · Informed (I): orchestrator