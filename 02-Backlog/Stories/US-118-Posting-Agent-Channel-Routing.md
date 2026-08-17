---
id: US-118
type: user-story
epic: EPIC-009
status: pending
priority: low
effort: M
created: 2026-08-17
assigned_to: unassigned
tags: [backlog, story, discord, posting, routing, agent]
---

# US-118: Posting Agent for Channel Routing Validation

## Story
**As a** trading system operator,
**I want** a posting agent that validates signal routing before dispatch,
**So that** stock signals never appear in the crypto channel and vice versa.

## Context
On 2026-08-17, stock signals were posted to the #crypto-setups channel due to a Python slicing bug (`list[-0:]` returns the full list). Fixed in commit `464198b` with:
1. Early return when 0 signals
2. Per-signal `asset_class` stamping + routing guard filter
3. Near-miss fallback removal

The code-level guard is the primary defense. A posting agent would be a second layer — an independent validation that runs after the pipeline produces payloads but before they hit Discord.

## Acceptance Criteria
- [ ] Agent reads the JSON output from portfolio_publish.py
- [ ] Validates every payload's `asset_class` matches the target channel
- [ ] Validates stock payloads → DISCORD_STOCK_CHANNEL_ID only
- [ ] Validates crypto payloads → DISCORD_CRYPTO_CHANNEL_ID only
- [ ] Blocks and alerts on any mismatch
- [ ] Logs all routing decisions for audit

## Notes
- Lower priority — the code-level routing guard (US-117 fix) is the primary defense
- Consider implementing as a post-publish verification step rather than a pre-publish gate
- Could also validate that no duplicate signals are posted across channels
