# Model Review Recommendations — Implementation Status

**Date**: 2026-09-30
**Source**: Weekly Model Assignment Review [T3], llm-stats channel

## 1. decay-watch-daily → T3 model
- **Priority**: Medium
- **Status**: ⚠️ Blocked — cron API doesn't support model field updates
- **Workaround**: Recreate the job with explicit `model: deepseek/deepseek-v4-flash`, or change profile default
- **Impact**: ~$0.02/job saved, ADR-001 compliance

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
- **Due**: 2026-10-17 (17 days from now)
- **Action**: Quarterly review per ADR-001 §2b — evaluate 10 trigger conditions for restrictiveness