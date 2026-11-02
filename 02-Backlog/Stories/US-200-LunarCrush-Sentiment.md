---
type: user-story
epic: EPIC-017
priority: P1
status: backlog
created: 2026-11-02
owner: coder
tags: [data, sentiment, lunarcrush, cost]
---

# US-200 — Confirm LunarCrush tier; add daily sentiment if free

## Description
`LUNARCRUSH_API_KEY` exists in `.env`. Confirm whether it is on a free tier. If free, add a daily sentiment ingest; if paid, report the cost and do NOT enable without approval.

## Acceptance Criteria
- Tier confirmed (free vs paid) from the LunarCrush API/account.
- If free: daily sentiment ingest wired + stored, labeled source=lunarcrush.
- If paid: no ingest enabled; cost reported to orchestrator for decision.

## Owner / RACI
- Owner (A): coder · Responsible (R): coder · Consulted (C): researcher · Informed (I): orchestrator (cost approval)