---
id: US-156
type: user_story
status: backlog
epic: EPIC-014-Tech-Debt
priority: medium
created: 2026-09-20
tags: [security, jev, architecture, plugins]
---

# US-156: Jev stays out-of-process

**As a** Hermes user who already has a working TypeSafe key,
**I want** to call Jev as an HTTP decision service instead of loading a community plugin in-process,
**so that** untrusted Python never runs inside the agent with my credentials.

## Acceptance Criteria

1. Default path is `curl`/script against `/v1/systemone`
2. No install-time scanner bypass
3. Session chat model is unchanged
4. Optional helper is a standalone script, not hooks on every turn

## Context

Already implemented: `jev_client.py` uses Python stdlib `urllib` for direct HTTP POST.
No plugin dependency. No hooks. Standalone Python module imported only when explicitly called.
This story is satisfied by the current architecture — logged here as a standing constraint
for any future Jev work.