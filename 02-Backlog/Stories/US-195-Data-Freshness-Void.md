---
type: user-story
epic: EPIC-017
priority: P0
status: backlog
created: 2026-11-02
owner: backtester
tags: [gauntlet, data, freshness, validity]
---

# US-195 — Data-freshness rule voids stale gate results

## Description
Any gate result computed while a required ingest was stale or failed is automatically void and flagged in the ledger.

## Acceptance Criteria
- Gate runs check the freshness of every required ingest before computing; a stale/failed dependency voids the result.
- Voided runs are written to the trials ledger with reason="stale_data", excluded from promotion but counted for G5.
- A freshness SLA per feed is enforced (see US-201 data inventory).

## Owner / RACI
- Owner (A): backtester · Responsible (R): coder · Consulted (C): risk-guardian · Informed (I): orchestrator