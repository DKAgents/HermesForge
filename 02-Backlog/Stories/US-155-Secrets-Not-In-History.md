---
id: US-155
type: user_story
status: backlog
epic: EPIC-014-Tech-Debt
priority: high
created: 2026-09-20
tags: [security, secrets, ops, key-management]
---

# US-155: Keys never appear in shell history or screenshots

**As a** person configuring TypeSafe on a server,
**I want** to add `TYPESAFE_API_KEY` without putting the secret on the command line,
**so that** a screenshot or history dump cannot leak a live key.

## Acceptance Criteria

1. Key is entered only in `~/.hermes/.env` via an editor
2. Setup docs do not use `echo 'TYPESAFE_API_KEY=...'`
3. If a key is exposed, rotation at the TypeSafe console is part of the same story

## Context

Current Jev integration (`jev_client.py`) reads from env file — already safe.
But the setup instructions in this session used `echo` with the key on command line.
Future: use `systemd-creds` or `hermes vault add` pattern for secret management.