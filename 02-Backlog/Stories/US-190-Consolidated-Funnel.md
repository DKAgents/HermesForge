---
type: user-story
epic: EPIC-017
priority: P0
status: backlog
created: 2026-11-02
owner: product-owner
tags: [gauntlet, funnel, reporting]
---

# US-190 — Consolidated per-gate funnel table

## Description
No single per-gate funnel tally exists today (gate results are spread across the trials ledger + registry + reports). Produce one consolidated funnel (entered / passed / failed per gate, top-3 failure reasons per gate) from the trials ledger + strategy registry. Regenerate weekly and post to the Strategy Status channel.

## Acceptance Criteria
- A script produces a per-gate funnel table from `data/gauntlet/trials.jsonl` + registry statuses (G0..G7: entered/passed/failed + top-3 failure reasons).
- Weekly cron regenerates it and posts to the Strategy Status channel.
- Funnel reconciles to actual ledger counts (115 trials) + registry statuses.

## Owner / RACI
- Owner (A): product-owner · Responsible (R): coder · Consulted (C): backtester · Informed (I): orchestrator