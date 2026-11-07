---
type: user-story
epic: EPIC-017
priority: P1
status: backlog
created: 2026-11-07
owner: coder
tags: [options, deribit, vrp, backfill, data, iv-surface]
---

# US-231 — Backfill Deribit options history for the VRP test

## Problem

HYP-30 (variance risk premium) needs historical option PREMIUMS + realized vol,
but the existing `ingest_deribit_iv.py` only forward-accumulates ~30d of ATM IV /
DVOL. The gauntlet cannot backtest the VRP on a month of data.

## Fix

Build `scripts/data/ingest_deribit_options_history.py` (or extend the existing
Deribit ingester) to backfill, via the FREE Deribit History API
(`https://history.deribit.com/api/v2/public`, no token, ~20 rps):

1. Enumerate expired BTC + ETH option instruments
   (`get_instruments?currency=BTC|ETH&kind=option&expired=true`).
2. Pull their trade history (`get_last_trades_by_instrument`), then reconstruct a
   daily ATM-straddle PREMIUM series (= call price + put price at the nearest-ATM
   strike per expiry) over the available history (BTC 2016+, ETH 2019+ — capture
   at least 2 years).
3. Pull realized vol (`get_historical_volatility`) and DVOL
   (`get_volatility_index_data`) for the vol-of-vol timing gate.
4. Store idempotently (PK dedup, skip-empty, never fabricate) — extend `iv_store.py`
   (or a new `options_history` store) with: per-day BTC/ETH ATM-straddle premium,
   underlying, DTE, realized vol, DVOL.

## Hard constraints

- Free / no-auth source only (Deribit History API + public REST); do NOT depend on
  a paid key or Tardis.dev.
- Idempotent + resumable (checkpointed, so a partial download resumes).
- Never fabricate IV/premiums; prefer Deribit-quoted `mark_iv` where available and
  flag any BS-inversion clearly.
- Path-scoped commits only; never `git add -A` / `git add .`.

## Acceptance Criteria

- A store exists with >= 2 years of daily BTC/ETH ATM-straddle premiums + realized
  vol + DVOL, dedup-safe, sourced from the free Deribit API.
- Backfill is resumable + idempotent (a second run inserts 0 new rows).
- The store is readable by the HYP-30 backtester.

## Owner / RACI
- Owner (A): coder · Responsible (R): coder · Consulted (C): backtester · Informed (I): orchestrator