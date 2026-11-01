---
type: user-story
epic: EPIC-014
priority: P1
status: backlog
created: 2026-11-01
tags: [data-source, crypto, hyperliquid]
---

# US-177 — Hyperliquid as the source of truth for all crypto history (forward)

## Problem

The full-window crypto backtests were re-run on OKX bars as a proxy, because Hyperliquid's public candle endpoint retains only ~17 days of 5m history. But we will trade crypto on Hyperliquid, so backtests must reflect Hyperliquid's actual liquidity, price volatility, and fills — not a cross-venue proxy.

## Fix

Make Hyperliquid the single source of truth for crypto bars going forward: accumulate a persistent local Hyperliquid bar store (daily ingestion of the universe at the trading resolution) so a full window of *same-venue* Hyperliquid history builds up over time and future backtests no longer need OKX as a proxy.

## Acceptance

- A persistent Hyperliquid bar store exists and is populated by a daily ingestion job.
- Crypto backtests read the same-venue Hyperliquid bars (falling back to the proxy only for the pre-store gap, clearly labeled).
- Documented retention/coverage so the "46-day OKX proxy" caveat disappears over time.