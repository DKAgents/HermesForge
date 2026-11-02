---
type: user-story
epic: EPIC-017
priority: P2
status: backlog
created: 2026-11-02
owner: backtester
tags: [gauntlet, gates, revalidation]
---

# US-210 — Re-run G1-died strategies under new G1

## Description
Strategies that died only at G1 may be re-run under the recalibrated G1 (US-207). Re-runs are new ledger trials and count toward DSR/PBO.

## Acceptance Criteria
- Eligible (G1-only-died) strategies identified and re-run under the new G1.
- Each re-run writes a fresh trials-ledger entry (new param_hash) and increments the G5 N.

## Owner / RACI
- Owner (A): backtester · Responsible (R): backtester · Consulted (C): researcher · Informed (I): orchestrator