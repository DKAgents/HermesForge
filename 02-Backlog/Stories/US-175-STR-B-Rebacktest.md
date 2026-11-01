---
type: user-story
epic: EPIC-014
priority: P1
status: backlog
created: 2026-11-01
tags: [strategy-validation, backtest]
---

# US-175 — STR-B realistic-fill re-backtest (the sole survivor)

## Problem

STR-B (MACD histogram divergence, stocks) is the only strategy whose edge survives realistic fills (OOS +1.25 R, t=10.6; factor-decomp alpha +0.84 R). But its magnitude is uncertain — Phase 1A shows decay (1.07→0.42→0.15 R) while walk-forward says +1.25 R; the discrepancy needs a realistic-fill re-backtest before any sizing rests on it.

## Fix

Re-backtest STR-B with realistic fills (corrected cost via fee_source + no look-ahead close entry, per US-172/173) to pin the magnitude.

## Acceptance

- A realistic-fill OOS figure for STR-B, with the Phase-1A-decay vs walk-forward discrepancy either reconciled or explicitly flagged.
- Honest verdict on whether a sizeable claim rests on it.