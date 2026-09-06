# US-130: Crosspost Job Overlap Evaluation

**Date:** 2026-09-06  
**Evaluator:** Publisher Agent (HermesForge)  
**Verdict:** REDUNDANT — Job 356f3c4fb973 is a strict subset of Job 61cccd31ed5c

---

## Jobs Evaluated

| Property | Job 356f3c4fb973 | Job 61cccd31ed5c |
|---|---|---|
| **Name** | Auto-Crosspost Daily Briefing | Webhook Crosspost All Channels |
| **Script** | `webhook_crosspost.sh` (71 lines) | `crosspost_webhook_all.sh` (213 lines) |
| **Schedule** | `5 13 * * 1-5` (Mon-Fri 13:05 UTC) | `*/5 * * * *` (every 5 min, all week) |
| **Frequency** | 1×/day (weekdays only) | 288×/day (12/hr × 24) |
| **Channels Covered** | 1: `1532020053548208328` (#daily-market-briefing) | 8: stock-setups, crypto-setups, daily-market-briefing, strategy-status, strategy-research, paper-trading, day-trade-crypto, day-trade-stocks |
| **Dedup Mechanism** | None (re-fetches latest message) | State file (`crosspost_state.json`) with atomic write |
| **Last 3 Runs** | All silent (empty output — already crossposted by Job 61cccd) | "Crosspost: 1 messages, 7 skipped" each cycle |

## Overlap Analysis

Both jobs crosspost from the same source channel `1532020053548208328` (#daily-market-briefing) to a follower channel via Discord webhook. The mechanism is identical — both use `curl` to fetch the latest message from the Discord API and forward it via webhook POST.

**Job 356f3c is a strict subset of Job 61cccd.** Every message that Job 356f3c would crosspost is already being crossposted by Job 61cccd, which runs 288× more frequently and covers all 8 channels including the one Job 356f3c targets.

Evidence: Job 356f3c's last 3 runs all produced empty output because Job 61cccd had already crossposted the daily briefing message. The state-file dedup in `crosspost_webhook_all.sh` prevents double-posting across runs.

## Timing Verification

| Event | Time | Actor |
|---|---|---|
| Market Intelligence post | 13:00 UTC Mon-Fri | Job 79c465c541f2 |
| Crosspost window (old) | 13:05 UTC Mon-Fri | Job 356f3c4fb973 (paused) |
| Crosspost window (current) | 13:00 or 13:05 UTC (every 5 min) | Job 61cccd31ed5c |

Job 61cccd runs at `*/5`, so it will pick up the Market Intelligence post at either 13:00 (race-dependent) or 13:05 (guaranteed next tick). This is the same effective crosspost window that Job 356f3c provided.

## Channel Coverage After Removal

| Channel ID | Channel Name | Covered by 61cccd? |
|---|---|---|
| 1528555538848153640 | stock-setups | ✅ |
| 1528555885310513213 | crypto-setups | ✅ |
| 1532020053548208328 | daily-market-briefing | ✅ (was the sole target of 356f3c) |
| 1533332485641998386 | strategy-status | ✅ |
| 1534834809451450409 | strategy-research | ✅ |
| 1537225420120793088 | paper-trading | ✅ |
| 1540951134200402071 | day-trade-crypto | ✅ |
| 1540951208028803142 | day-trade-stocks | ✅ |

**No channel will miss crossposts.** All 8 channels remain covered by Job 61cccd31ed5c running every 5 minutes.

## Action Taken

1. **Paused** Job 356f3c4fb973 (`hermes cron pause 356f3c4fb973`) — status confirmed `[paused]`
2. **Archived** `webhook_crosspost.sh` → `/root/HermesForge/reports/campaigns/2026-09-aegis-rebuild/archived-webhook_crosspost.sh` — preserved for reference, not deleted
3. **No changes** to `crosspost_webhook_all.sh` or Job 61cccd31ed5c

## Files Modified

| File | Action |
|---|---|
| `/root/.hermes/scripts/webhook_crosspost.sh` | Deprecated (copy archived; original kept for rollback) |
| `/root/HermesForge/reports/campaigns/2026-09-aegis-rebuild/archived-webhook_crosspost.sh` | Created (archival copy) |

## Rollback

If any channel misses a crosspost after removal, re-enable with:
```
hermes cron resume 356f3c4fb973
```

## Conclusion

Job 356f3c4fb973 is redundant. Its sole function (crossposting #daily-market-briefing at 13:05 on weekdays) is fully subsumed by Job 61cccd31ed5c which does the same thing every 5 minutes for all 8 channels, with a stronger dedup mechanism. No channel coverage gap exists.