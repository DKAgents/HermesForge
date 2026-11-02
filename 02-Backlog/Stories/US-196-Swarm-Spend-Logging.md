---
type: user-story
epic: EPIC-017
priority: P0
status: backlog
created: 2026-11-02
owner: coder
tags: [cost, observability, swarm]
---

# US-196 — Log swarm (ad-hoc agent) spend alongside cron spend

## Description
`usage_audit.jsonl` tracks cron-only. Log ad-hoc swarm sessions (coder/architect/backtester/risk-guardian/researcher) so total monthly spend is visible per agent.

## Acceptance Criteria
- A per-agent spend record (model + tokens + cost) is captured for ad-hoc swarm dispatches, joined with cron spend.
- A single spend report shows total monthly cost broken down by agent (cron jobs AND swarm).
- The reported total reconciles to OpenRouter billing within a stated tolerance.

## Owner / RACI
- Owner (A): coder · Responsible (R): coder · Consulted (C): orchestrator · Informed (I): product-owner