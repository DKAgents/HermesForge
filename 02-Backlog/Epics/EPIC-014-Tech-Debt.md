---
id: EPIC-014
type: epic
status: in-progress
created: 2026-08-07
tags: [tech-debt, infrastructure, backlog]
---

# EPIC-014: Tech Debt and Infrastructure Quirks

Tracks known bugs, infrastructure quirks, and workarounds that affect HermesForge operations. These are not feature requests but documented issues that need permanent fixes or ongoing awareness.

## Stories

| Story | Status | Description |
|-------|--------|-------------|
| [[US-097]] | backlog | headroom_retrieve unreliable (upstream bug #1077) |
| [[US-098]] | backlog | hermes config set CLI bug for list-valued keys (#16493) |
| [[US-099]] | backlog | write_file silent truncation guard |
| [[US-100]] | backlog | send_message drops text when MEDIA included in same call |

## Notes

- All items in this epic have documented workarounds (see individual stories)
- These are low-frequency but high-impact: when they trigger, they cause silent failures or data loss
- Priority is lower than feature work but should not be forgotten
