# US-124: 30-Day Cost Summary

**Campaign:** 2026-09-aegis-rebuild  
**Generated:** 2026-09-07T02:00 UTC (approx)  
**Display TZ:** America/Los_Angeles  
**Methodology:** Token estimates from prompt sizes + typical response lengths × published OpenRouter pricing. No actual billing data available — these are planning estimates.

---

## LLM Cost (OpenRouter, 30-day)

| Job | Tier | Runs/30d | Est. In | Est. Out | $/Run | $/30d |
|-----|------|----------|---------|----------|-------|-------|
| Vault Connection Weaver | T2 | 180 | 12,000 | 2,000 | $0.0066 | **$1.18** |
| Trade Monitor | T3 | 720 | 3,000 | 800 | $0.0002 | $0.17 |
| Market Intelligence | T3 | 22 | 12,000 | 3,000 | $0.0009 | $0.02 |
| External Edge Discovery | T3 | 12 | 12,000 | 2,500 | $0.0009 | $0.01 |
| Autonomous Strategy Pipeline | T3 | 12 | 10,000 | 3,000 | $0.0008 | $0.01 |
| Performance Report | T3 | 30 | 5,000 | 1,000 | $0.0004 | $0.01 |
| LinkedIn Post Generator | T3 | 8 | 15,000 | 4,000 | $0.0012 | $0.01 |
| Vault Maintenance | T3 | 30 | 3,000 | 500 | $0.0002 | $0.01 |
| Connection Discovery | T3 | 30 | 8,000 | 1,500 | $0.0006 | $0.01 |
| Research/Model/ADR/Position | T3 | ~20 | 3,000 | 800 | $0.0002 | $0.00 |
| **Total (LLM crons)** | | | | | | **~$1.45** |

### Orchestrator sessions (not in cron)

Orchestrator runs on T2 (`deepseek-v4-pro`). Typical session: 20K input + 5K output = $0.012. At ~30 sessions per month: **~$0.36/mo**.

### Summary

| Tier | Monthly |
|------|---------|
| T1 (claude-opus-4.8) | $0.00 — never used |
| T2 (deepseek-v4-pro) | **$1.54** (weaver $1.18 + orchestrator ~$0.36) |
| T3 (deepseek-v4-flash) | **$0.27** (all other agents) |
| **Total** | **~$1.81/mo** |

### Cost per category

| Category | Monthly |
|----------|---------|
| Vault knowledge (weaver + connection discovery) | $1.25 |
| Trading (monitor + performance + strategies) | $0.20 |
| Market intelligence (briefing + edge discovery) | $0.03 |
| Content (LinkedIn) | $0.01 |
| Infrastructure (vault maintenance + ADR checks) | $0.01 |
| Orchestrator sessions | $0.36 |

---

## No-agent jobs (10 — $0.00/mo)

1. STR-Q Intraday Sweep Capture (`*/5`)
2. Daily Signal Scanner (14:45)
3. Paper Trading Capture A/B/D (14:50)
4. Daily Git Push (03:00)
5. Cron Watchdog (`*/15`)
6. Webhook Crosspost All Channels (`*/5`)
7. Trade Journal Daily Snapshot (03:00)
8. Weekly Restore Drill (Sunday 08:00)
9. Daily F&G Fetch (11:00)
10. (Auto-Crosspost Daily Briefing — paused, US-130)

---

## Cost optimization opportunities

1. **Vault Connection Weaver → T3** — the weaver runs 180×/month at T2 ($1.18). If T3 quality is acceptable for wikilink generation, this saves ~$1.12/mo (95% of T2 cost). Requires a quality comparison on 10 runs.

2. **Trade Monitor cadence** — 720 runs/month at T3 is the highest-frequency LLM cron. But at $0.17/mo total, the savings from reducing cadence are trivial. Keep as-is.

3. **Chart cache purge** — 807 MB, 8,497 files. Not a cost issue (disk), but a maintenance issue. A daily purge cron would reclaim ~500 MB on weekends.

4. **No-agent ratio** — 10 of 22 active jobs are already no-agent (45%). Remaining LLM agents are all doing judgment work that can't be scripted.

---

## Disk cost

- **Used:** 49 GB / 240 GB (22%)
- **Largest consumer:** signal_charts (807 MB)
- **Growth rate:** ~100-200 MB/month (cron output + market data + journal)
- **Runway at current rate:** >10 years before disk pressure

**No cost pressure on disk.** All data under 50 GB total.