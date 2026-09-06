---
id: US-128
epic: EPIC-014
type: story
status: story-ready
created: 2026-09-06
tags: [backlog, story, robustness, fear-greed, fail-closed, p1]
campaign: 2026-09-aegis-rebuild
train: 0
priority: P1
owner_profile: no-agent
model_floor: no-agent
---

# US-128 — Fear & Greed freshness check + fail-closed regime gate

- **Train:** 0
- **Priority:** P1
- **Owner profile:** no-agent
- **Model floor:** no-agent
- **Status:** story-ready
- **Campaign:** 2026-09-aegis-rebuild

## Story

As the regime-gated sizing logic, I need the Fear & Greed feed's freshness
verified before it is used, and regime-conditional sizing to fail closed on a
stale feed, so that a silently stale feed cannot quietly change position sizing.

## Background

Evidence from campaign `2026-09-aegis-rebuild`:

- `data-manifest.md`: `fear_greed_last_ok: unknown`.
- Protocol Phase C flags "stale feeds that disable regime logic (Fear & Greed)."
- Regime conditioning feeds into strategy sizing (see US-121 background: regime
  backfill into trades.csv was itself flagged as unvalidated).

## Acceptance

- [ ] A no-agent freshness check records `fear_greed_last_ok` into the data
      manifest on each fetch and flags staleness beyond a defined threshold.
- [ ] When the feed is stale/missing, regime-conditional sizing FAILS CLOSED —
      it falls back to the conservative default (never a larger size), and the
      condition is logged/alerted.
- [ ] The check is no-agent (mechanical); no LLM in the path.
- [ ] Test specified: inject a stale timestamp; assert regime logic falls back
      conservative and the staleness is recorded.
- [ ] Rollback specified.

## Forbidden

- No live-soul edits
- No publisher-file edits unless owner is publisher
- No truncate/replace of history files
- No change to the 1% cap; fail-closed may only REDUCE size
- No credentials in repo or report output

## Rollback

Freshness gate is additive. Disable it to revert to current behavior. Fail-closed
default is strictly more conservative, so leaving it on is safe.
