---
type: user-story
epic: EPIC-017
priority: P1
status: backlog
created: 2026-11-02
owner: coder
tags: [data, backfill, hyperliquid, cost]
---

# US-198 — Backfill 5m history (HL S3 archive, capped $20)

## Description
Backfill 5m history via the Hyperliquid public S3 archive (requester-pays). Estimate cost BEFORE pulling; cap the backfill at $20 unless explicitly approved. Fallback: OKX public candles as a proxy for the same coins, labeled proxy.

## Acceptance Criteria
- Cost estimate produced before any pull; hard cap $20 enforced without approval.
- Backfilled bars land in the store with `source` labeled (hyperliquid vs okx_proxy).
- Report: coins covered, bar depth achieved, final cost, and any proxy-labeled gaps.

## Owner / RACI
- Owner (A): coder · Responsible (R): coder · Consulted (C): backtester · Informed (I): orchestrator (cost approval)