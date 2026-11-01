---
type: user-story
epic: EPIC-016
priority: P0
status: backlog
created: 2026-11-01
tags: [data, positioning, liquidation, open-interest]
---

# US-186 — Liquidation + open-interest positioning feed

## Problem

Funding carry only becomes *predictive* when conditioned on where the leverage is and when it is forced out. We ingest funding rates (US-179) but lack the positioning context — open interest, long/short ratio, and liquidation levels/events — that turns a raw funding reading into a signal.

## Fix

Ingest into a persistent store:
- Open interest (and per-side OI / long-short ratio where available) from Hyperliquid `metaAndAssetCtxs`.
- Liquidation events / liquidation levels (Hyperliquid websocket `liquidation` stream, or a documented source).
- Funding skew context alongside the existing funding store.

## Acceptance

- A positioning store + daily/hourly ingestion cron (via resolve_python.sh, no_agent), idempotent.
- funding_carry (US-185) can consume OI + liquidation data as conditioning features.