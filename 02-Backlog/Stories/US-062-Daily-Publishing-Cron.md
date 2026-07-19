---
id: US-062
epic: EPIC-009
type: story
status: backlog
created: 2026-07-20
points: 5
tags: [discord, cron, scanner, publishing, automation]
depends-on: US-058, US-059, US-060, US-061
---

# US-062: Daily Scanner → Discord Publishing Cron

## Story
As a strategy operator, I want the signal scanner to run automatically each trading day and publish qualifying setups to Discord, so that I receive alerts without any manual intervention.

## Acceptance Criteria
- [ ] Script `scripts/discord/daily_publish.py` that:
  1. Loads universe and cached OHLCV data (refreshes stale data via fetch_data.py)
  2. Runs enabled scanners (strategies with `publish_enabled: true`)
  3. For each signal: checks deduplication, generates chart, posts to Discord
  4. Prints summary: N signals found, N posted, N skipped (duplicates), N errors
- [ ] Hermes cron job created: runs daily at 09:45 AM ET (14:45 UTC) on weekdays
  - Schedule: `45 14 * * 1-5`
  - Delivers summary report to Discord #stock-setups channel
- [ ] Dry-run mode: `python3 daily_publish.py --dry-run` runs full pipeline without posting
- [ ] Error handling: if chart generation fails for one signal, log error and continue (do not abort full run)
- [ ] Rate limiting: add 2-second delay between Discord posts to avoid rate limits
- [ ] Environment variables required: `DISCORD_STOCK_CHANNEL_ID`, `DISCORD_CRYPTO_CHANNEL_ID`
  stored in `~/.hermes/.env`

## Cron Job Config
```
Schedule: 45 14 * * 1-5  (9:45 AM ET weekdays — after market open, after overnight data settled)
Script: scripts/discord/daily_publish.py
Delivery: discord:#stock-setups (summary only)
Toolsets: terminal
```

## Definition of Done
- daily_publish.py runs end-to-end in dry-run without errors
- Hermes cron job created and confirmed with hermes cron list
- At least one real signal posted to Discord in live test
- Committed to main
