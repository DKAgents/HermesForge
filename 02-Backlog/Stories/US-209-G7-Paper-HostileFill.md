---
type: user-story
epic: EPIC-017
priority: P1
status: backlog
created: 2026-11-02
owner: architect
tags: [gauntlet, gates, g7, adr]
---

# US-209 — G7: forward validation on paper with Hostile Fill model

## Description
G7 unchanged except: forward validation runs as paper using the Hostile Fill model until a human approves a live venue. (G2–G6 unchanged.)

## Acceptance Criteria
- G7 forward validation uses the Hostile Fill model (bar-level realistic fills), never the optimistic paper ledger, until human live approval.
- ADR records the G7 clarification (paper-with-hostile-fill until human go-live).

## Owner / RACI
- Owner (A): architect · Responsible (R): coder · Consulted (C): backtester, risk-guardian · Informed (I): orchestrator