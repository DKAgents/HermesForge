---
id: US-127
epic: EPIC-013
type: story
status: story-ready
created: 2026-09-06
tags: [backlog, story, effectiveness, strategy-factory, seeder, p2]
campaign: 2026-09-aegis-rebuild
train: 3
priority: P2
owner_profile: coder
model_floor: T2
---

# US-127 — Coded strategy seeder feeding the reject-heavy filter

- **Train:** 3
- **Priority:** P2
- **Owner profile:** coder
- **Model floor:** T2
- **Status:** story-ready
- **Campaign:** 2026-09-aegis-rebuild

## Story

As the strategy pipeline, I need a coded candidate seeder so generation is
systematic rather than ad-hoc, while keeping the reject-heavy filter and Risk
Guardian promotion gates intact, so that "0% ship" reflects a real edge bar and
not a starved input.

## Background

Evidence from campaign `2026-09-aegis-rebuild`:

- `failure-log.md` line 4: "Strategy pipeline 0% ship (filter, not factory)."
- BACKLOG_INDEX shows the pipeline HAS shipped WATCH-tier strategies
  (US-113/114/115/120/122), each walk-forward OOS, deployed WATCH at 0.5% risk.
  So the filter works; what is missing is a coded *seeder* — candidate
  generation is ad-hoc, not a factory.
- A reject-heavy filter with real expectancy gates and a seeder is the acceptable
  shape (protocol Phase C). Do NOT weaken the gates to raise ship rate.

## Acceptance

- [ ] A coded seeder enumerates candidate strategies from defined generators
      (parameter sweeps, regime templates, edge hypotheses) on a schedule.
- [ ] Seeder output feeds the existing reject-heavy filter unchanged; expectancy
      / walk-forward / Risk Guardian gates are NOT relaxed.
- [ ] Promotion past WATCH requires Risk Guardian APPROVE/CONDITIONAL and
      walk-forward OOS evidence; 1% cap untouched.
- [ ] Ship-rate metric defined and reported (candidates in → WATCH → promoted).
- [ ] Test specified: seeder produces N candidates, K are rejected by the filter
      for the stated reasons; assert gates fire.
- [ ] Rollback specified.

## Forbidden

- No live-soul edits
- No publisher-file edits unless owner is publisher
- No truncate/replace of history files
- No relaxation of the 1% cap or promotion gates
- No credentials in repo or report output

## Rollback

Seeder is an additive input job. Disable it and the pipeline reverts to ad-hoc
candidate entry. No data migration.
