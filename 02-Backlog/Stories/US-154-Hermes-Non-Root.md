---
id: US-154
type: user_story
status: backlog
epic: EPIC-014-Tech-Debt
priority: critical
created: 2026-09-20
tags: [security, vps, root, hardening]
---

# US-154: Hermes must not run as root

**As a** VPS operator,
**I want** Hermes and any Jev helper to run as an unprivileged user,
**so that** a plugin, hook, or leaked key cannot take over the whole machine.

## Acceptance Criteria

1. Hermes home, `.env`, and the gateway process belong to a non-root user
2. `TYPESAFE_API_KEY` is mode 600 and unreadable by other users
3. No plugin with `pre_tool_call` / session hooks is required to call Jev
4. Direct `POST https://api.typesafe.ai/v1/systemone` still works

## Context

Currently running as root. Jev integration uses direct HTTP from Python stdlib — no plugin dependency.