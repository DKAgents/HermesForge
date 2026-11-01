# US-175 — STR-B Realistic-Fill Re-Backtest (Magnitude Pin)

**Backtester agent | 2026-11-01 | Read-only on pipeline code**
Harness exercised: `scanners.scanner_b_macd_divergence.run_backtest` (next-open
fill via `market_structure.compute_pullback_entry`) + `gauntlet.fee_source`
(3 bp stock round-trip, US-172). Full universe = 530 cached stock tickers,
2019-01-01 → 2026-10-30.

---

## 1. The honest realistic-fill figure

Charged: next-open entry (US-173) + 3 bp stock cost (US-172). Exit = the
standard `_walk_forward_exit` (intrabar high/low, stop capped at −1R, time-stop
at 15 bars) — the same realistic exit model the discovery runner has used since
US-115.

| Configuration | N | Net R/trade | t-stat | 95% CI | Win % |
|---|---|---|---|---|---|
| **Bidirectional** (all signals) | 2877 | **+0.144** | 5.29 | [0.091, 0.197] | 41.2% |
| **Long-only** (live stocks config) | 637 | **+0.383** | 6.33 | [0.266, 0.504] | 48.4% |

- Frictionless (pre-cost) bidirectional = 0.157 R; the 3 bp cost drags only
  **0.0127 R/trade** — the US-172 cost correction is negligible for stocks.
- Long-only ≈ 80 signals/year.

**STR-B's pinned realistic OOS figure is ~+0.38 R/trade (long-only) or
~+0.14 R/trade (bidirectional) — NOT +1.25 R.**

---

## 2. Reconciliation: decay (1.07→0.42→0.15) vs walk-forward (+1.25 R)

The two headline numbers are **not a magnitude disagreement to reconcile — they
are both artifacts of the same superseded code path**, and neither survives the
fill-realism corrections. The magnitude is driven almost entirely by the exit
model, which changed at US-115 (Aug 16), *before* the "sole survivor" claim and
*before* the US-172/173 fixes.

### 2.1 Measured magnitude collapse (from the CSVs)

| Version | Date | Fill | Exit model | Avg R | r_multiple range |
|---|---|---|---|---|---|
| Pre-US-115 (`STR-B-macd-…-phase1a.csv`) | Jul 29 | close (look-ahead) | naive | 0.881 | −22.97 … +24.72 |
| US-115 v3 (`STR-B-stocks-phase1a-v3.csv`) | Aug 16 | close (look-ahead) | realistic | 0.170 | −1.00 … +6.36 |
| **This re-run (US-173 + US-172)** | Nov 1 | **next-open** | realistic | **0.157** (raw) | −1.00 … +6.36 |

Decomposition of the corrections:

- **US-115 realistic exit** (0.881 → 0.170): **−0.71 R — the dominant fix.**
- **US-173 next-open fill** (0.170 → 0.157): −0.013 R (minor).
- **US-172 3 bp cost** (0.157 → 0.144 net): −0.013 R (minor).

### 2.2 Why pre-US-115 was inflated

The Jul-29 CSV's exit distribution is the smoking gun:

- Only **5.9 %** of exits hit target (184 / 3126); **45 %** exited on "time",
  with r_multiple drifting to **±25 R**.
- Mean +0.88 vs median **−0.68**: the number is carried by a few unbounded
  time-exit winners, priced off look-ahead close entries. Remove that and the
  magnitude collapses ~5×.

### 2.3 The "decay" does not exist under realistic fills

Per-year net R (frictionless R shown; cost is ~−0.013 uniformly):

    2019 +0.056   2020 +0.050   2021 +0.312   2022 +0.414
    2023 −0.074   2024 +0.135   2025 +0.140   2026 +0.392

Sub-period buckets (frictionless): 2019-21 = 0.142, 2022-23 = 0.120,
2024+ = 0.199. The 1.07→0.42→0.15 monotone decay is gone — it was an artifact
of the naive-exit/close-entry model that disproportionately inflated the early,
higher-volatility years. What remains is noisy/cyclical, weakly positive.

### 2.4 Walk-forward (+1.25 R) cannot be reproduced

Two independent reasons:

1. **Stale code path.** The OOS +1.25 (t=10.6) was computed 2026-08-01/02 with
   the **pre-US-115** scanner (close-entry + naive exit, where `scan()` still
   emitted `r_multiple`). US-115 (Aug 16) moved exit simulation into
   `run_backtest` and `scan()` no longer returns `r_multiple`.
2. **Broken integration (flag, not fixed — read-only).** `walk_forward.py`
   `scan_with_params` calls `scan()` then `apply_costs()`, which defaults a
   missing `r_multiple` to 0. Re-running `walk_forward.py --strategy B` today
   would score every STR-B signal at ≈ 0 − cost_r — garbage. The harness needs
   a fix (`scan_with_params` must route STR-B through `run_backtest`), which I
   did not make per the read-only constraint.

---

## 3. Verdict — what does sizing rest on?

**No sizeable position/sizing claim can rest on STR-B's magnitude.** The figure
that would have justified a sizeable allocation (+1.25 R, "robust edge") was
produced by a close-entry, naive-exit implementation that is now superseded.

The honest, realistic-fill expectancy is:

- **Long-only (the live config): +0.38 R/trade**, t = 6.3, CI [0.27, 0.50].
- **Bidirectional: +0.14 R/trade**, t = 5.3, CI [0.09, 0.20].

What survives is a **robust but small positive sign**, not a large magnitude:

- The sign is solid: positive in 7 of 8 years, +ve t-stat in both configs, and
  the win-rate (48 % long-only) is respectable.
- The magnitude is ~**3× below** +1.25 for long-only and ~**9× below** for
  bidirectional.

**Recommendation:** treat STR-B as a modest-expectancy strategy (~0.4 R/trade
long-only). Any position sizing previously justified off +1.25 R must be
scaled down to reflect the realistic figure, and the +1.25 "robust edge" label
in the Aug-01 walk-forward report should be struck as superseded.

---

## Appendices

- Raw trade-level output: `/root/.hermes/cache/scratch/strb_rebacktest_trades.csv`.
- Driver (read-only caller, uses only pipeline functions):
  `/root/.hermes/cache/scratch/strb_rebacktest.py`.

### Caveats

- Survivorship bias (current S&P constituents) is unchanged and unaddressed.
- 3 bp cost is an IBKR-tier broker assumption; slippage beyond the 1 bp
  assumption and gap-through stops (capped at −1R) would reduce the figure
  further — the numbers above are an upper bound, not a conservative one.
- The independent factor-decomposition alpha (+0.84 R, t=12.6) cited in the
  brief was **not** re-run here and is subject to the same fill-convention
  question; it should be re-derived on the next-open/realistic-exit trade tape
  before being used to support any claim.