---
type: user-story
epic: EPIC-017
priority: P0
status: backlog
created: 2026-11-02
owner: coder
tags: [ops, cron, watchdog, alerting]
---

# US-194 — Cron watchdog verifies artifacts, alerts on failure streak

## Description
The watchdog must verify actual job output/artifacts (not `last_status`, which agent-wrapped crons lie about), and alert to Discord on any failure streak ≥ 2.

## Acceptance Criteria
- Watchdog checks real artifacts (file mtimes, row counts, non-empty stdout) per job, not `last_status`.
- Discord alert fires on any failure streak ≥ 2 with the actual error.
- Verified: the streak=29 Signal Scanner failure would have alerted on day 2, not silently for 29 days.

## Owner / RACI
- Owner (A): coder · Responsible (R): coder · Consulted (C): risk-guardian · Informed (I): orchestrator