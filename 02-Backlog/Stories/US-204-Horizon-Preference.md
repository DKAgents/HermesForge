---
type: user-story
epic: EPIC-017
priority: P1
status: backlog
created: 2026-11-02
owner: researcher
tags: [hypothesis, horizon, intake]
---

# US-204 — Horizon preference 4h–7d

## Description
Prefer 4h–7d horizons. Intraday 5m seeds require an explicit argument that gross edge clears 4× all-in taker cost, or a maker-only execution plan.

## Acceptance Criteria
- Intake tags horizon; 5m seeds gate on a documented gross-edge-vs-4×-cost argument or a maker-only plan.
- 5m seeds lacking that argument are rejected before G0.

## Owner / RACI
- Owner (A): researcher · Responsible (R): coder · Consulted (C): backtester · Informed (I): orchestrator