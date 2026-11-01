---
type: user-story
epic: EPIC-016
priority: P1
status: backlog
created: 2026-11-01
tags: [validation, governance, research]
---

# US-183 — Harden the validation harness

## Problem

The literature the research surfaced (Harvey-Liu-Zhu, McLean-Pontiff, multiple-testing) shows most published "predictors" are data-mining artifacts that decay ~30%+ post-publication. Our current validation lacks the harsh-set checks that would catch this.

## Fix

Harden the validation harness to require, for every strategy before promotion:
- Deflated Sharpe Ratio (DSR) / multiple-testing correction (not raw Sharpe).
- Post-publication + post-2005 samples (where applicable).
- Locked walk-forward holdouts + a minimum-regime-performance floor (edge must hold across ≥2 regime partitions, not one bull/bear window).
- No-trade zones + partial-rebalancing cost-aware construction baked in.

## Acceptance

- The validation harness emits DSR + regime-partition stats; a strategy failing any harsh-set check cannot promote.
- Fed into the US-174 G3 gate (complementary, not duplicative).