---
type: user-story
epic: EPIC-017
priority: P1
status: backlog
created: 2026-11-02
owner: architect
tags: [gauntlet, gates, adr]
---

# US-207 — G1 recalibration: size-relative capacity + power floor

## Description
Replace G1's fixed capacity minimums ($250k 5m notional, $50k depth, ≥15 symbols) with size-relative checks: planned max order at the $10K stage must be ≤1–2% of top-5 depth within 10 bps. Replace the fixed ≥200-signal rule with a statistical-power minimum for the strategy's expected effect size. **Requires a new ADR before any threshold change takes effect.**

## Acceptance Criteria
- A new ADR records the G1 threshold change (size-relative + power floor) before it is applied.
- G1 checks scale with target size (≤1–2% of top-5 depth at $10K stage).
- Signal minimum is derived from statistical power for the expected effect size, not a fixed 200.

## Owner / RACI
- Owner (A): architect · Responsible (R): coder · Consulted (C): backtester, risk-guardian · Informed (I): orchestrator