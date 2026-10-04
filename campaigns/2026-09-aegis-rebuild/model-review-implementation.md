# Model Review Recommendations — Implementation Status

**Date**: 2026-09-30
**Source**: Weekly Model Assignment Review [T3], llm-stats channel

## 1. decay-watch-daily → T3 model
- **Priority**: Medium
- **Status**: ✅ Fixed — pinned to T3 via `hermes cron edit --model deepseek/deepseek-v4-flash`
- **Note**: Cron API tool can't set models; CLI `hermes cron edit --model` works. Job ID: 58bccfa185b5

## 2. Auto-Crosspost Daily Briefing
- **Priority**: High
- **Status**: ✅ Fixed — switched from no_agent script to agent-based
- **Root cause**: `DISCORD_BOT_TOKEN` in .env is dead (401 Unauthorized)
- **Fix**: Cron now uses Hermes native Discord tools to fetch + webhook to post

## 3. Hostile Fill Report timeout
- **Priority**: Low
- **Status**: ✅ Resolved — one-off Sep 27 timeout. Ran fine Sep 28-29. Monitor.

## 4. T1 Escalation Trigger Review
- **Priority**: Low
- **Due**: 2026-10-17
- **Status**: ✅ Completed 2026-10-04 (early)
- **Findings**: Zero T1 calls in 2.5 months. All 10 triggers kept — restrictiveness is correct. $55.37 saved via T3 migration. 91% T3 / 9% T2 distribution. Next review: 2027-01-17.