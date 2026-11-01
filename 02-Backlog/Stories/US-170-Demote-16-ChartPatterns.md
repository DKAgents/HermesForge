---
type: user-story
epic: EPIC-014
priority: P0
status: backlog
created: 2026-11-01
tags: [strategy-status, demotion]
---

# US-170 — Demote 16 chart-pattern "LIVE" strategies

## Problem

Sixteen chart-pattern strategies (STR-R, STR-T, STR-U, STR-V, STR-W, STR-AB, STR-AG, STR-AJ, STR-X, STR-Z, STR-AA, STR-AC, STR-AD, STR-AE, STR-AF — the US-114 "PASS" block) were promoted to LIVE on *frictionless* close-entry R-multiples (0.08–0.22 R) that are smaller than realistic friction (~0.1–0.3 R). The re-evaluation (cache/backtester_reevaluation_report.md) confirms they are hidden losers.

## Fix

Demote these 16 from LIVE/WATCH to "no claimable edge — needs friction re-backtest" in `regime_strategy_selector.py` and any strategy-file frontmatter/status registration that declares them LIVE. Do not delete — re-grade.

## Acceptance

- None of the 16 remain registered LIVE/WATCH.
- Their status reflects "no claimable edge (frictionless eval)" with a pointer to the re-evaluation report.