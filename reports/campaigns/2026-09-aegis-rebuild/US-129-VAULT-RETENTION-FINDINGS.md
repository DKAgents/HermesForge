# US-129 — Vault Maintenance Retention Audit Findings

**Date:** 2026-09-06  
**Investigator:** product-owner (T3)  
**Source:** read-only inspection of `maintain_vault.py`, `daily_publish.py`, `trade_log.py`, `snapshot_restore.py`, and `~/.hermes/cron/output/`

---

## 1. Purge Paths Discovered

Three active purge mechanisms were found. Two are in code. One is absent.

### Path A: Cron output purge (`maintain_vault.py:389–404`)

```python
cutoff_ts = time.time() - (14 * 86400)
for f in cron_out.rglob("*"):
    if f.is_file():
        if f.stat().st_mtime < cutoff_ts:
            f.unlink()
```

- **Target:** `~/.hermes/cron/output/*` (all 21 cron job output directories)
- **Retention:** 14 days from last-modification time
- **Files currently on disk:** 379 files, 1.4 MB
- **Files purgeable right now:** 7 (oldest: 14.7 days)
- **Files from the Sep 1–5 trade-log loss window:** 104 files across 14 job directories
- **First purge of Sep 1 evidence:** 2026-09-15
- **Last purge of Sep 5 evidence:** 2026-09-19

### Path B: Chart cache purge (`daily_publish.py` — `purge_old_charts()`)

- **Target:** `~/.hermes/signal_charts/*`
- **Retention:** 48 hours (CHART_RETENTION_HOURS=48)
- **Files on disk:** 7,994 files, 759 MB
- **RCA relevance:** LOW — charts are regenerated on demand from cached price data. Not forensic evidence.

### Path C: Vault maintenance logs (NO PURGE)

- **Target:** `04-ForgeLoop/Maintenance/*.md`
- **Files on disk:** 52 files (oldest: 2026-07-17)
- **Retention:** NONE — `maintain_vault.py` writes these but never deletes them.
- **RCA relevance:** MEDIUM — each log records changed-file count and step status. Useful for establishing vault state over time.

### NOT purged (safe)

| Path | Files | Relevance |
|------|-------|-----------|
| `07-Risk/INCIDENT_LOG.md` | 33 lines | HIGH — incident records |
| `07-Risk/GUARDIAN_DECISIONS.md` | exists | HIGH — governance audit |
| `scripts/paper_trading/snapshots/snapshot-*.d/` | journal + CSV + crosspost_state | HIGH — US-126 recovery |
| `04-ForgeLoop/Maintenance/` | 52 files | MEDIUM — vault state history |
| `~/.hermes/vault_index/` | checkpoint + dedup + FTS | LOW — rebuildable |
| `~/.hermes/memory/` | MEMORY.md + USER.md | LOW — Hermes manages these |

---

## 2. Retention Gap: Cron Evidence vs Snapshot Horizon

| Mechanism | Retention | Horizon |
|-----------|-----------|---------|
| Cron output purge | **14 days** | Sep 1 files gone by Sep 15 |
| US-126 snapshots | **35 days** | Sep 1 files survive until Oct 6 |
| **GAP** | **21 days** | Cron evidence destroyed before snapshots age out |

The 14-day purge window is explicitly shorter than the 35-day snapshot
retention mandated by US-126.  Cron execution records — which are the PRIMARY
forensic evidence for post-incident analysis (like the Sep 1–5 trade log
loss) — are destroyed 21 days before the snapshot archive ages out.

### Concrete example

The Sep 1–5 trade log loss produced NO backup. If a similar incident occurred
today, the only evidence would be in the cron output directories (STR-Q sweep
logs, Trade Monitor summaries, Daily Scanner output). Under the current purge
rules:

- **Day 1–14:** Evidence exists in `~/.hermes/cron/output/`
- **Day 15–35:** Evidence is GONE. Snapshots still exist but snapshots do NOT
  include cron output. Journal + CSV are recoverable but cron execution context
  (what the sweep saw at each 5-min tick, what Trade Monitor detected) is lost.
- **Day 36+:** Snapshots age out per US-126 retention. Nothing remains.

### What the snapshots protect

Current snapshot payload (from `snapshot_restore.py`):
- `trade_journal.jsonl` (append-only trade events)
- `trades.csv` (derived projection)
- `manifest.txt` (sha256 + row count)
- `crosspost_state.json` (US-131)

**The snapshots do NOT include:**
- `~/.hermes/cron/output/` (cron execution records)
- `04-ForgeLoop/Maintenance/` (vault state history)
- `07-Risk/INCIDENT_LOG.md` (incident records)

---

## 3. RCA-Sensitive Cron Output Directories

These directories contain evidence that would be needed for post-incident
forensics on a trading data loss or pipeline failure:

| Job ID | Name | Files in Sep 1–5 | RCA Value |
|--------|------|------------------|-----------|
| `b9fb0afb1e29` | STR-Q Sweep | (every 5 min, 288/day) | CRITICAL — price data, exit detection, CLOSED events |
| `d1e07c3f4543` | Trade Monitor | 29 files | HIGH — swing trade exits, entry detection |
| `3f49a07a2f04` | Daily Scanner | 5 files | HIGH — daily signal generation |
| `4b178ecc02cd` | Paper Trading Capture | 5 files | HIGH — signal capture |
| `79c465c541f2` | Market Intelligence | 4 files | LOW — market context |
| `cb22b038a6d6` | Performance Report | 5 files | MEDIUM — PNL at time of incident |
| `65dfc591efad` | Cron Watchdog | records | MEDIUM — health checks during incident |
| `61cccd31ed5c` | Webhook Crosspost | records | LOW — crosspost activity |
| `9d77b5c75db7` | Vault Maintenance | 5 files | LOW — this job's own purge records |

---

## 4. Follow-Up Stories Required

### US-133: Extend cron output retention to ≥35 days (coder, P1)

Change `maintain_vault.py:392` from `14 * 86400` to `35 * 86400` (or the
`RETENTION_DAYS` constant from `snapshot_restore.py`). This aligns cron
evidence retention with the snapshot horizon. No new purge logic — just
one constant change.

**Risk:** 1.4 MB total cron output today. At 35-day retention, expect ~3.5 MB.
Trivial on a 240 GB disk.

### US-134: Add cron output to snapshot payload (coder, P2)

Add `~/.hermes/cron/output/` to the `snapshot_restore.py` snapshot payload.
The snapshot directory would grow from ~290 KB to ~3.5 MB. Optional: compress
cron output as `.tar.gz` in the snapshot dir. This closes the forensic gap
entirely — even after 35 days, the snapshot archive preserves the evidence.

### US-135: Add vault maintenance logs and incident log to snapshot (coder, P3)

Add `04-ForgeLoop/Maintenance/` and `07-Risk/INCIDENT_LOG.md` to the snapshot
payload. These are small (52 files, ~208 KB; 33 lines) and provide context
about vault health and known incidents at the time of each snapshot.

---

## 5. Verdict

- **Cron output retention IS shorter than the snapshot horizon (14d vs 35d).**
- **This is a confirmed gap.** The 21-day window between cron-evidence purge
  and snapshot expiration means forensic context is silently destroyed.
- **The gap is real but the risk is bounded:** trade-event data is now
  protected by the append-only journal + US-126 snapshots. Cron output is
  diagnostic context, not the source of truth.
- **No code changes in this story** (investigation only, per US-129 spec).
  Follow-up stories US-133/US-134/US-135 filed for implementation by the
  appropriate profile owners.

**Rollback:** N/A — this is an investigation. No production state was modified.