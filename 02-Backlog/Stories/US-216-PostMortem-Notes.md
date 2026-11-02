---
type: user-story
epic: EPIC-017
priority: P1
status: backlog
created: 2026-11-02
owner: researcher
tags: [feedback, postmortem, knowledge]
---

# US-216 — Post-mortem note per failed strategy

## Description
Every failed strategy gets a one-paragraph post-mortem in the vault (gate, reason, and what would have to be true for a variant to pass), which the generators read.

## Acceptance Criteria
- A post-mortem note (gate, root reason, variant-conditions) is written for each failed strategy.
- Post-mortems are indexed + retrievable by the generation crons.
- Backfill post-mortems for the already-failed class (STR-Q, 16 chart-patterns, funding directional, raw xsmom).

## Owner / RACI
- Owner (A): researcher · Responsible (R): documenter · Consulted (C): backtester · Informed (I): orchestrator