---
type: user-story
epic: EPIC-017
priority: P1
status: backlog
created: 2026-11-02
owner: coder
tags: [data, websocket, hyperliquid, realtime]
---

# US-199 — Persistent websocket listener for metaAndAssetCtxs

## Description
Stand up a persistent websocket listener for `metaAndAssetCtxs` (OI, mark/oracle basis, funding) so that history accumulates continuously rather than hourly snapshots only.

## Acceptance Criteria
- A persistent process (systemd/daemon, not a cron) streams `metaAndAssetCtxs` into the assetctx store continuously.
- No data loss on reconnect (backfill the gap on reconnect before appending).
- Verified: minute-level (or finer) basis/OI history accumulates with no gaps over a 24h soak.

## Owner / RACI
- Owner (A): coder · Responsible (R): coder · Consulted (C): architect · Informed (I): orchestrator