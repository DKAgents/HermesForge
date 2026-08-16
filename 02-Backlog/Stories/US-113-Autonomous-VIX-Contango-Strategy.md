---
id: US-113
epic: EPIC-013
title: Autonomous Pipeline — VIX Contango Breakout strategy (deployed)
status: done
created: 2026-08-16
completed: 2026-08-16
tags: [strategy, autonomous-pipeline, walk-forward, paper-trading, vix]
---

# US-113 — Autonomous Pipeline: VIX Contango Breakout strategy (deployed)

## Summary

The HermesForge Autonomous Strategy Pipeline (cron) processed staged edge
candidate `CAND-20260816-vix-contango-persistence`, coded a scanner, ran Phase
1A + walk-forward validation, and deployed the validated strategy to paper
trading at WATCH-level risk.

## Story

**As** the trading research swarm,
**I want** staged edge candidates to be autonomously coded, backtested, and
walk-forward-validated,
**so that** strategies with genuine out-of-sample edge reach paper trading
without manual bottlenecks, while weak candidates are killed early.

## Work Done (2026-08-16, autonomous cron run)

- Enriched VIX term-structure cache (full ^VIX + ^VIX3M history 2018-2026) via
  `scripts/validation/cache_vix_term_structure.py`.
- Coded `scanner_vix_vrp_contango.py` (20-day breakout gated by persistent VIX
  contango: IVTS ≤ 0.92, VIX ≤ 20, ≥60% of prior 90d contango).
- Extended `run_phase1a.py` with `--scanner`/`--crypto`/`--json` + p-value.
- Phase 1A: 15,518 signals, mean R +0.093, p=0.0, 3/3 sub-periods (thin edge).
- Walk-forward (net of costs): OOS pooled mean R +0.103, p=0.0 → ROBUST EDGE.
- Deployed to paper trading: `STR-VIXC-vix-contango-breakout` at 0.5% risk
  (WATCH), suppressed in `risk_off` regimes.
- Vault note: `06-Strategies/Hypotheses/STR-20260816-vix-vrp-contango-breakout.md`.

## Acceptance Criteria

- [x] Scanner coded and committed.
- [x] Phase 1A run with p-value; mean R > 0 and p < 0.10.
- [x] Walk-forward OOS mean R > 0 and OOS p < 0.10.
- [x] Added to capture_signals.py, position_sizing.py, regime_strategy_selector.py.
- [x] Vault note created.
- [x] Candidate frontmatter updated to `watch`.
- [x] Backlog index updated.

## Notes / Risks

- Edge is regime-fragile: 2022-bear OOS window mean R −0.336; 2025 OOS flat.
  Suppressed in risk_off; live-paper review required to promote beyond WATCH.
- Two sibling candidates processed in the same run were marked `backtest_failed`
  (sector-momentum-continuation; cross-asset-sentiment-divergence crypto-F&G proxy).
