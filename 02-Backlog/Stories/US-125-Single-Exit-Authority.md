---
id: US-125
epic: EPIC-014
type: story
status: story-ready
created: 2026-09-06
tags: [backlog, story, robustness, exit-authority, split-brain, p0]
campaign: 2026-09-aegis-rebuild
train: 0
priority: P0
owner_profile: coder
model_floor: T2
---

# US-125 — Single exit authority: resolve STR-Q 5m vs Trade Monitor 60m split

- **Train:** 0
- **Priority:** P0
- **Owner profile:** coder
- **Model floor:** T2
- **Status:** story-ready
- **Campaign:** 2026-09-aegis-rebuild

## Story

As the paper-trading system, I need exactly one process authorized to close any
given open position so that a trade cannot be closed twice, closed with
conflicting exit reasons, or left half-closed by a race between the two
schedules.

## Background

Evidence from campaign `2026-09-aegis-rebuild`:

- `failure-log.md` line 3: "Split exit paths: STR-Q 5m vs swing Trade Monitor
  60m."
- Two crons act on open positions: STR-Q Intraday Sweep Capture `b9fb0af`
  (*/5, no-agent) and HermesForge Trade Monitor `d1e07c` (every 60m, T3).
- `trade_log.close_trade` (trade_log.py:263) raises on double-close, which
  prevents the *worst* corruption — but two schedulers racing on the same open
  row is a split-brain: whichever fires first wins, exit reason/price depend on
  timing, and the loser's intended close is silently dropped.

## Acceptance

- [ ] A single documented exit authority per open trade. Either (a) Trade
      Monitor owns all closes and the STR-Q sweep emits only entry / stop-adjust
      signals; or (b) an explicit `closer` ownership key on each open row so
      exactly one process may close it. Decision recorded in an ADR draft.
- [ ] No code path allows two schedulers to both attempt a close on the same
      open `trade_id`.
- [ ] Exit-alert SLA stated (max latency from exit condition to Discord alert)
      and assigned to its owner. Alert code stays publisher-owned.
- [ ] Test specified: simulate STR-Q sweep and Trade Monitor firing on the same
      open position in the same window; assert exactly one close, deterministic
      exit reason.
- [ ] Rollback specified.

## Forbidden

- No live-soul edits
- No publisher-file edits unless owner is publisher (exit-ALERT code is
  publisher's; this story changes close AUTHORITY, not alert rendering)
- No truncate/replace of history files
- No credentials in repo or report output

## Rollback

Gate the ownership change behind a flag. If closes regress, revert to current
behavior (both crons active, double-close guard in `close_trade` as the
backstop). No data migration required.
