---
type: user-story
epic: EPIC-017
priority: P1
status: backlog
created: 2026-11-08
owner: coder
tags: [copytrading, leaderboard, fills, reverse-engineering, on-chain]
---

# US-232 — Pull HL leaderboard + top-trader fills + consistency screener

## Problem

The systematic search exhausted price/positioning/flow/options classes (one real
edge: the funding carry). The untested path is to follow the edge that DEMONSTRABLY
exists in other traders. Hyperliquid is fully on-chain — every trader's fills and
positions are public and free. We need to pull the leaderboard + top traders' fill
history and rank them by genuine CONSISTENCY (not raw PnL) as reverse-engineering
candidates.

## Fix

Build `scripts/research/hl_leaderboard_scan.py` (or similar) that:

1. Pulls the HL leaderboard (top traders by PnL across time windows). Nail the
   correct `info` request type (probe `{"type":"leaderboard","timeWindow":...}`
   across "1d"/"7d"/"30d"/"allTime"; the plain type without a window failed with
   "Failed to deserialize"). Endpoint: `https://api.hyperliquid.xyz/info`, POST,
   Content-Type application/json, a browser User-Agent.
2. Pulls `userFills` + `userFillsByTime` for the top ~50–100 traders (fills carry
   coin, px, sz, side A/B, dir, closedPnl, fee, crossed, liquidation, time — this
   is the reverse-engineering corpus). `userFillsByTime` = up to 10k fills.
3. Builds a CONSISTENCY screener that ranks traders by a real metric, NOT raw PnL:
   - all-time ROI (≥ some bar), still-active (recent 30d ROI > 0),
   - trade count (enough sample, not one lucky trade),
   - no single "freak" day (daily ROI within a sane band),
   - drawdown / profit-factor from their closedPnl series.
4. Stores the ranked leaderboard + each screened trader's fills (idempotent, resumable).
5. Emits a ranked top-10 list with metrics for the reverse-engineering step.

## Hard constraints

- Free / no-auth HL public info API only.
- Idempotent + resumable (checkpointed; rate-limit aware — the info endpoint is
  rate-limited).
- Never fabricate fills/positions; skip empty/error responses.
- Path-scoped commits only; never `git add -A` / `git add .`.

## Acceptance Criteria

- Leaderboard pulled + top traders identified.
- A consistency screener (ROI + trade count + no-freak-day + drawdown) ranks them;
  raw-PnL-alone is NOT the ranking.
- Top ~10 traders' fills stored, ready for reverse-engineering.
- Report the ranked top-10 with their consistency metrics.

## Owner / RACI
- Owner (A): coder · Responsible (R): coder · Consulted (C): researcher · Informed (I): orchestrator