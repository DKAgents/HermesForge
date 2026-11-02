---
type: user-story
epic: EPIC-017
priority: P1
status: backlog
created: 2026-11-02
owner: researcher
tags: [hypothesis, dedupe, ledger]
---

# US-206 — Dedupe seeds against trials ledger (by mechanism)

## Description
Dedupe every new seed against the trials ledger by mechanism (not just name) before registration, so the same economic mechanism is not re-run under a new label.

## Acceptance Criteria
- Intake checks the ledger for a mechanism match before registration.
- A near-duplicate mechanism is linked to its prior trial (and requires a pre-registered variant argument) rather than silently re-registered.
- Verified: a renamed re-skin of a failed mechanism is flagged, not silently re-run.

## Owner / RACI
- Owner (A): researcher · Responsible (R): coder · Consulted (C): backtester · Informed (I): orchestrator