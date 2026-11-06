---
type: user-story
epic: EPIC-017
priority: P2
status: backlog
created: 2026-11-06
owner: coder
tags: [execution, fill-realism, calibration, gauntlet, g3]
---

# US-228 — Calibrate G3 fill-realism against empirical fill data

## Problem

G3 fill-realism currently uses a *guessed* pessimistic model (maker fill_prob =
0.35, adversarial taker selection, flat slippage assumptions). This is the ONE
place the "are we testing too aggressively?" concern is legitimate — but it only
affects *marginal* edges. The flat nulls we observe (HYP-16 H1 ratio 1.002,
p=0.46; negative gross medians) fail on *signal absence*, before any fill model
touches them. The honest fix is to calibrate the fill model against empirical
data, NOT to loosen the gates.

## Fix

1. Build an empirical fill model: use real L2 order-book snapshots to *walk the
   book* for a given order size, producing actual slippage + fill probability
   rather than a flat assumption.
2. Calibrate G3's fill model against that empirical distribution.
3. Keep the pessimistic model as a conservative fail-closed fallback until
   calibration is complete (never silently switch to an *optimistic* fill).

## Data dependency

L2 book history lives in `s3://hyperliquid-archive/market_data/{date}/{hour}/
l2Book/{coin}.lz4` (currently SCP-blocked from this AWS account — see session
notes). NON-AWS PATH FOUND (2026-11-06): Ironflow API `/v1/trades` + `/v1/fills`
expose tick-level fills with maker/taker role + fee + execution price, ~12 months
rolling — actual execution data is a MORE direct calibration source than book
depth (no "walk the book" modeling needed). Kaggle `datastore90/hyperliquid-
historical-data` also carries L2 snapshots. Prefer Ironflow fills; flag if
unavailable. Do NOT fabricate fill data.

## Acceptance Criteria

- G3 fill-realism is calibrated against empirical L2 data (or the blocker is
  documented with a concrete unblock path).
- Fill-model pessimism is data-grounded, not guessed.
- The flat nulls are unaffected (they fail on signal, not fills); marginal
  edges can be re-evaluated with the calibrated model.

## Owner / RACI
- Owner (A): coder · Responsible (R): coder · Consulted (C): backtester, risk-guardian · Informed (I): orchestrator