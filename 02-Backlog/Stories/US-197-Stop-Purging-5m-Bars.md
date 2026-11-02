---
type: user-story
epic: EPIC-017
priority: P1
status: backlog
created: 2026-11-02
owner: coder
tags: [data, bars, retention]
---

# US-197 — Stop purging 5m bars; retain all going forward

## Description
5m bars currently have ~17-day retention (store purging). Stop purging; retain all 5m bars going forward so the persistent Hyperliquid bar store accumulates continuously.

## Acceptance Criteria
- The 5m bar store stops deleting old bars; retention is unbounded (bounded only by disk).
- Verified: a bar older than the previous purge horizon remains queryable.
- Documented disk-growth estimate (see US-201 inventory).

## Owner / RACI
- Owner (A): coder · Responsible (R): coder · Consulted (C): backtester · Informed (I): orchestrator