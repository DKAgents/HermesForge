---
type: user-story
epic: EPIC-016
priority: P0
status: backlog
created: 2026-11-01
tags: [execution, cost, fill-model]
---

# US-180 — Execution-layer drag fix

## Problem

The forensic diagnosis found the −1.86 R/trade stop drag is a *structural defect*, not an immovable fee: trade-through entries adversarially select entries (you only fill after the reversal ends), tight stops make one tick of slippage a large fraction of R, and worst-print fills turn −1 R nominal into −2.86 R actual. This is the highest-ROI fix — it would drag a *dumb* signal from −1.79 R toward coin-flip-minus-fee (~−0.3 R).

## Fix

Redesign the execution model in the paper pipeline (hostile-fill model) to compress the drag:
- Wider stops to lower the fee-per-R fraction (subject to the existing 1% position-size cap — no risk increase).
- Limit entries at the swept level instead of chasing trade-through.
- Market-vs-limit exit choice (limit exits when liquidity allows, market when the stop must fill).

## Acceptance

- The new execution model measurably reduces the per-stop drag (quantified vs the current −2.86 R stop / −1.79 R average).
- The accounting/dynamic-fee correctness from US-164..168 is preserved (this changes fill *choice*, not the cost math).