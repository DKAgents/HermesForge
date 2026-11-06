---
type: pre-registration
hypothesis_id: HYP-16
purpose: robustness sweep (confirm-or-refute the null, NOT a hunt for success)
committed_before_run: true
date: 2026-11-06
---

# HYP-16 robustness sweep (pre-registered)

## Purpose

HYP-16's primary run returned a flat null (H1 ratio 1.002, p=0.46; H2 net edge
~+1.1bps over SMA-only control). Before closing it, confirm the null is STABLE
across economically-motivated parameter variations — the opposite of a
sensitivity "hunt for a win."

## Fixed variations (all pre-committed; no post-hoc additions)

The following 3 variations, each tested in isolation against the HYP-16
baseline (OI >= 90th pct trailing 90d; close > SMA20; exit close < SMA or 5-bar
time stop):

- **V-A (slower trend):** SMA20 -> SMA50. Everything else identical.
- **V-B (looser OI):** 90th pct -> 80th pct. Everything else identical.
- **V-C (tighter OI):** 90th pct -> 95th pct. Everything else identical.

## Interpretation rule (pre-committed)

- If H1 (extreme-OI |move| vs baseline) stays ~1.00 with p >> 0.05 across V-A/B/C,
  the null is CONFIRMED ROBUST -> close HYP-16 with higher confidence.
- If H2 net edge stays <= SMA-only control across all variations, the OI filter
  adds nothing -> CONFIRMED.
- A variation that genuinely FLIPS (large effect, not marginal) is reported
  honestly, but is NOT promoted without a fresh independent out-of-sample test
  on held-out data (a robustness sweep is not an edge discovery).

## Hard rules (unchanged)

Same data (HF OI at ~/.hermes/market_data/hl_oi_hf/), same native-perp universe,
45bps fail-closed taker, no look-ahead, no leverage, LIVE off, one trials-ledger
entry per variation with fresh param_hash, path-scoped commit.
