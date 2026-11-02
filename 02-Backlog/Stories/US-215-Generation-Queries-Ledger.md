---
type: user-story
epic: EPIC-017
priority: P1
status: backlog
created: 2026-11-02
owner: researcher
tags: [feedback, generation, ledger]
---

# US-215 — Generation crons query the trials ledger

## Description
The generation crons (Autonomous Strategy Pipeline, External Edge Discovery, Edge Factory, Weekly Research) must query the trials ledger before proposing seeds: avoid mechanisms that failed G4/G5, bias toward mechanisms that passed G3 or later.

## Acceptance Criteria
- Each generation cron reads the ledger (failed/negative mechanisms) before proposing.
- New proposals cite prior-trial outcome for similar mechanisms.
- Verified: a mechanism that failed G4/G5 is not re-proposed without a pre-registered variant argument.

## Owner / RACI
- Owner (A): researcher · Responsible (R): coder · Consulted (C): backtester · Informed (I): orchestrator