---
type: user-story
epic: EPIC-016
priority: P0
status: backlog
created: 2026-11-01
tags: [alpha, funding-rate, carry, crypto]
---

# US-185 — Funding carry: full-universe executable construction + fix sizing/basis/kill

## Problem

The US-179 funding-carry validation (reports/backtester/funding_carry_validation.md) found the "+0.64 R" edge was **54% basis** (concentrated in XRP/kSHIB/CRV/SOL, non-spot-available), the delta-neutral hedge was backtested on a 35-coin universe where it cannot be executed, the stop's `basis_widen` used a compressed `fundingHistory premium` proxy instead of the real mark-oracle basis, and **"1R" was actually $1,000 = 0.1% of capital** (not the 1% the spec claims). The naive "spot-available only" fix is wrong — the principal wants the FULL Hyperliquid universe tradeable (long and short).

## Fix

1. Reconstitute funding carry to be executable on the FULL HL universe:
   - **Delta-neutral** (long spot / short perp) where spot exists.
   - **Directional short-perp** elsewhere — receive funding when it is high-positive, with the price risk modeled and gated (funding must exceed directional risk).
   Do NOT artificially restrict to spot-available coins.
2. Decompose the edge: keep the **funding** component (tradeable everywhere, directional-or-hedged); source the **real mark-oracle basis** (from `assetCtxs`) or exclude the suspect basis-only term — do not let a proxy basis inflate the number.
3. Fix the sizing: 1R = 1% risk on notional, not 0.1% of capital.
4. Fix the `basis_widen` kill-stop to use the real mark-oracle basis.

## Acceptance

- Funding carry is executable + correctly modeled on the full HL universe (long/short possible on every listed perp).
- The edge decomposes honestly into funding vs basis; the basis proxy no longer dominates.
- Re-validated with correct sizing + real basis, and a stated honest net edge (expected ~+0.4–0.6 R/position on the executable subset, ~10–15%/yr net).