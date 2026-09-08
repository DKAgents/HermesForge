---
id: US-140
epic: EPIC-014
type: story
status: story-ready
created: 2026-09-07
priority: P3
tags: [backlog, story, efficiency, disk, chart-cache, no-agent]
campaign: 2026-09-aegis-rebuild
train: 1
owner_profile: no-agent
model_floor: no-agent
points: 1
depends_on: []
---

# US-140 — Close the signal_charts purge gap (826 MB / 8,497 files)

- **Train:** 1
- **Priority:** P3
- **Owner profile:** no-agent
- **Model floor:** no-agent
- **Status:** story-ready
- **Campaign:** 2026-09-aegis-rebuild

## Story

As the operator, I need chart PNGs purged on a reliable schedule so that a
transient artifact cache does not accumulate unbounded across weekends and long
holidays.

## Background

Evidence from campaign `2026-09-aegis-rebuild` (second pass, 2026-09-07 UTC):

- FACT: `/root/.hermes/signal_charts` is **826 MB across 8,497 files** — 33% of
  all used disk and the single largest directory (`inventory.yaml` data_roots;
  `du -sh` confirmed 826M live).
- FACT: charts are transient (48-hour intended retention), purged inside
  `daily_publish.py`. inventory note: "Bloated — 8K files, 800MB. Long-weekend
  purge gap."
- INFERENCE: coupling the purge to `daily_publish.py` means the purge only runs
  when publishing runs; multi-day gaps (weekends, holidays, a skipped publish)
  let the cache balloon. This is a maintenance/robustness issue, not a cost one
  — 181 GB free, no disk pressure (>10-year runway per `cost-30d.md`).

Low priority precisely because there is no disk pressure. Filed so the
maintenance gap is tracked rather than rediscovered.

## Acceptance

- [ ] A standalone no-agent purge (its own cron or a watchdog step) removes
      chart PNGs older than the retention window (48h, or a stated value)
      independent of whether `daily_publish.py` ran.
- [ ] Purge is idempotent and logs count/bytes reclaimed to stdout.
- [ ] Retention window documented; no publisher embed/chart-generation code is
      modified (this purges outputs, it does not touch chart creation).
- [ ] After one run on the current cache, directory drops toward the steady
      state (a few hundred MB, not 800+).

## Forbidden

- No live-soul edits
- No publisher-file edits — chart *generation* is publisher-owned; this story
  only deletes aged output files, it must not alter how charts are produced
- No truncate/replace of history files (charts are not history)
- No credentials in output

## Rollback

Disable the purge cron/step; charts revert to publish-coupled purge (current
behavior). Deleted aged charts are regenerable on next publish.
