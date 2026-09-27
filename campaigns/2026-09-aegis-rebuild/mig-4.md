# MIG-4: Move 05-Proposals → trading/proposals

**Date**: 2026-09-27

**Moved**: `05-Proposals/` → `trading/proposals/` (contains only
`PROP-001-hermes-strategy-gauntlet.md`).

**Verified safe**: No scripts read `05-Proposals/` — only campaign audit
docs referenced it (updated in this commit). No cron jobs, no scanners,
no capture pipelines depend on the path.

**Rollback**: `git revert` of this commit.