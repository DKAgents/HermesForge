---
type: user-story
epic: EPIC-017
priority: P0
status: backlog
created: 2026-11-02
owner: coder
tags: [ops, cron, stability]
---

# US-192 — Root-cause and fix failing crons

## Description
Root-cause and fix the four degraded jobs found in the diagnostic: Daily Signal Scanner (streak=29), Paper Trading Capture (A/B/D) (streak=2), F&G Fetch (streak=2), Confidence Digest (delivery_failed).

## Acceptance Criteria
- Each job posts root cause + fix; failure streaks return to 0.
- Read the actual cron output files (not last_status) to confirm real output resumes.
- No recurring error in the following 3 scheduled runs.

## Owner / RACI
- Owner (A): coder · Responsible (R): coder · Consulted (C): risk-guardian · Informed (I): orchestrator