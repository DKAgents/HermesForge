---
type: user-story
epic: EPIC-017
priority: P1
status: backlog
created: 2026-11-02
owner: researcher
tags: [data, inventory, documentation]
---

# US-201 — Data inventory note

## Description
Produce a data inventory note in the vault: every feed, history depth, freshness SLA, and which hypotheses each feed enables.

## Acceptance Criteria
- A vault note enumerates each feed (venue, endpoint, fields, granularity, depth, refresh/SLA, source label).
- Each feed is mapped to the hypotheses/strategies it unblocks (e.g. funding → HYP-01, IV → US-181, bars → xsmom).
- Proxies (OKX-for-HL) and gaps (no HL liquidation/L-S OI) are explicitly flagged.

## Owner / RACI
- Owner (A): researcher · Responsible (R): researcher · Consulted (C): coder (ground truth) · Informed (I): orchestrator