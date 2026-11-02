---
type: user-story
epic: EPIC-017
priority: P2
status: backlog
created: 2026-11-02
owner: orchestrator
tags: [cost, compute, rebalance]
---

# US-217 — Cut Auto-Crosspost + Vault Weaver spend ≥50%

## Description
Auto-Crosspost Daily Briefing ($7.71/30d) and Vault Connection Weaver ($4.63/30d) are the top two cron spend items. Cut combined spend by ≥50% (lower frequency or cheaper tier) without breaking publishing.

## Acceptance Criteria
- Combined monthly spend for the two jobs drops ≥50% (from ~$12.3/30d baseline).
- Publishing output (briefing crosspost + vault weaver) remains functional.
- Reported net $ change.

## Owner / RACI
- Owner (A): orchestrator · Responsible (R): coder · Consulted (C): publisher · Informed (I): product-owner