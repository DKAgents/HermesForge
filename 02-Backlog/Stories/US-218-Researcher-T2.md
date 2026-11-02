---
type: user-story
epic: EPIC-017
priority: P2
status: backlog
created: 2026-11-02
owner: orchestrator
tags: [cost, routing, researcher]
---

# US-218 — Researcher hypothesis-generation to T2; report cost change

## Description
Move the researcher's hypothesis-generation step to T2. Report the net monthly cost change (generation quality up at higher tier vs incremental token cost).

## Acceptance Criteria
- Hypothesis-generation step runs at T2 (`deepseek-v4-pro-0813`).
- Net monthly cost delta reported (before/after).
- Routed through the swarm; trading agents do not write code.

## Owner / RACI
- Owner (A): orchestrator · Responsible (R): coder · Consulted (C): product-owner · Informed (I): researcher