---
type: user-story
epic: EPIC-017
priority: P1
status: backlog
created: 2026-11-02
owner: researcher
tags: [hypothesis, intake, frontmatter]
---

# US-202 — Required hypothesis frontmatter (incl. counterparty)

## Description
Every hypothesis must carry required frontmatter: `hypothesis_id`, `source` (human|council|web|generated), `venue`, `instruments`, `horizon`, entry/exit logic, expected gross edge (bps), cost hurdle, data dependencies, and `counterparty` — who is on the other side and why they structurally accept the loss. Seeds missing any field (especially counterparty) are rejected before G0.

## Acceptance Criteria
- Intake validates all required fields; missing field (esp. `counterparty`) → reject before G0.
- The hypothesis template (used by scraper/generator agents) enforces these fields.
- Verified: a seed without `counterparty` is rejected at intake, not at a later gate.

## Owner / RACI
- Owner (A): researcher · Responsible (R): coder · Consulted (C): risk-guardian · Informed (I): orchestrator