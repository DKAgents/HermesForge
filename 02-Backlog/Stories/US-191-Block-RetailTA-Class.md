---
type: user-story
epic: EPIC-017
priority: P0
status: backlog
created: 2026-11-02
owner: risk-guardian
tags: [gauntlet, intake, signal-class, safety]
---

# US-191 — Stop STR-Q + block retail-TA/ICT-SMC class at intake

## Description
Stop paper trading STR-Q and all chart-pattern / retail-TA / ICT-SMC strategies. Block that entire signal class at intake (fast-fail before G0), not just in the skill prior.

## Acceptance Criteria
- STR-Q and all chart-pattern/retail-TA/ICT-SMC strategies removed from paper-trading rotation (no new trades).
- A hard intake gate rejects this signal class before G0 (code-level, not skill-prior-only).
- Verified: scan output shows zero new retail-TA signals.

## Owner / RACI
- Owner (A): risk-guardian · Responsible (R): coder · Consulted (C): researcher · Informed (I): orchestrator