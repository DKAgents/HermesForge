---
type: user-story
epic: EPIC-016
priority: P1
status: backlog
created: 2026-11-01
tags: [data, basis, cross-venue, funding]
---

# US-188 — Cross-venue basis feed

## Problem

The tradeable funding/basis spread is *cross-venue* (Hyperliquid vs OKX vs Binance), not the single-venue mark-oracle deltas we currently accumulate. We only have the HL side, so the actual carry arb spread is not measurable.

## Fix

Ingest cross-venue funding + price basis into a store:
- Hyperliquid funding + price (already have) joined to OKX funding + price (Binance/Bybit are 403, per standing note — do not retry them).
- Compute the HL-vs-OKX funding spread + price basis per coin.

## Acceptance

- A cross-venue basis store + ingestion cron (no_agent, resolve_python.sh), idempotent.
- funding_carry (US-185) can consume the cross-venue spread as the real carry metric.