---
id: EPIC-009
type: epic
status: in-progress
created: 2026-07-20
updated: 2026-07-20
tags: [epic, discord, signals, publishing, charts]
---

# EPIC-009: Discord Signal Distribution

## Goal

Automatically publish rich trade setup alerts to Discord when the scanner identifies a valid signal. Alerts include strategy metadata, trade details, and a Python-generated chart image. Strategy-level publish control is managed via frontmatter flags in each strategy note.

## Why This Comes Before Auto-Execution

Signal distribution to Discord serves as the human review layer between scanner output and live trading. It allows the user to monitor signal quality, catch edge cases the scanner misses, and build confidence in the strategy before enabling auto-execution. It is also independently useful as a trading alert system even if auto-execution is never enabled.

## Stories

| Story | Title | Status |
|-------|-------|--------|
| US-058 | Strategy Frontmatter — Publish Control Fields | ⬜ Backlog |
| US-059 | Chart Image Generator | ⬜ Backlog |
| US-060 | Discord Alert Formatter and Publisher | ⬜ Backlog |
| US-061 | Signal Deduplication Log | ⬜ Backlog |
| US-062 | Daily Scanner → Discord Publishing Cron | ⬜ Backlog |

## Definition of Done
- Scanner runs daily, identifies signals, posts rich alerts to correct Discord channel
- Chart images generated on VPS, posted as attachments
- No duplicate alerts for the same setup within 5 trading days
- Publish control flags on strategy notes gate which strategies post
- All strategy notes updated with publish_enabled and publish_channel fields

## Out of Scope
- Auto-execution (EPIC-008)
- TradingView MCP chart integration
- Real-time intraday scanning (daily bars only)
