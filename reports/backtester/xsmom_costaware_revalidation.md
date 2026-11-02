# US-182 Cost-aware Cross-sectional Momentum — net-edge re-validation (REAL data)

Date: 2026-11-02
Author: Coder (HermesForge), run via `scripts/gauntlet/revalidate_xsmom.py`
Scope: cost-aware cross-sectional momentum (`xsmom.py`, spec architect_us182_spec.md),
LONG-FLAT (F1), BTC 200-DMA overlay (F6). Every number below is REAL output on
4 years of same-venue Hyperliquid 1d bars (1461 bars/coin). No promotion, no
store mutation, no paper-forward deferral.

## 0. Data reality — root-cause findings (read first)

The architect spec's driving constraint (§0 fact 3) claimed "DAILY candles are
retained DEEP (980+ bars/coin)" **on disk**. That is FALSE on this machine:

- `~/.hermes/market_data/hl_bars/bars_1d.db` is **EMPTY** (0 bars, 0 tickers);
  `bars_1h.db` is also empty. Only `bars_5m.db` has data (~17.5 days).
- Root cause: `scripts/data/ingest_hl_bars.py` hardcodes `INGEST_TIMEFRAMES = ["5m"]`
  and explicitly excludes 1d on a **false dependency** — the comment "1d is
  intentionally EXCLUDED (already ingested deep by fetch_crypto_data.py)", but
  `fetch_crypto_data.py` **does not exist** in the repo. Daily bars were therefore
  never persisted.
- The OKX proxy fallback for 1d is ALSO broken: `okx_proxy.fetch_okx_bars` passes
  the HL timeframe `"1d"` straight through, but OKX requires `"1D"` (uppercase) —
  the live endpoint answers `code=51000 Parameter bar error` for `bar=1d`, so
  `load_bars("1d")` returns an empty frame.

Hyperliquid's `candleSnapshot` endpoint itself serves the daily bars **deep and
same-venue**: 1461 bars/coin for the majors (BTC/ETH/SOL/… back to 2022-11-03),
≥ 438 for every backtest name. This driver therefore fetches HL 1d **directly**
(read-only, one call per name) instead of via `load_bars`, so the panel is 100%
Hyperliquid-sourced and the F13 provenance floor is met by construction.

> These two data-path defects (1d-store never ingested; okx_proxy `1d`→`1D`
> bug) are FILED as follow-ups, not fixed inline — they are outside US-182's
> code-commit scope and touch ground-truth modules the spec mandates READ-only.

Backtest universe = 31 names (`CRYPTO_UNIVERSE` minus kBONK/kPEPE/kSHIB/PAXG),
panel 1461 days × 31 names (2022-11-03 → 2026-11-02).

## (a) Current momentum rank (30d lookback, skip 1d) — REAL

The 2026-11-02 window is a broad drawdown: **every** name has negative 30d
momentum, so the "long leg" is simply the least-negative names.

| rank | name | mom | σ(ann) | leg |
|---|---|---|---|---|
| 1 | HYPE | -1.61% | 59.0% | LONG |
| 2 | ZEC | -5.41% | 91.9% | LONG |
| 3 | TRX | -6.66% | 47.4% | LONG |
| 4 | BTC | -7.54% | 28.5% | LONG |
| 5 | BNB | -9.45% | 40.6% | LONG |
| 6 | BCH | -11.04% | 68.3% | LONG |
| 7 | NEAR | -11.35% | 136.2% | |
| … | (24 more) | … | | |

Momentum is the verbatim §1.1 score `P[t-1]/P[t-30] - 1` (skip=1 drops the most
recent bar; with lookback=30 this is a 29-day return from the skipped bar).

## (b) Partial rebalance vs naive full-turnover — REAL

Unit of observation = one weekly holding period (180 episodes over 4.0 years).
`1R = 1% capital`; `net_r` already nets the 12-bps turnover cost once.

| config | n | turnover | mean net R | net Sharpe | PF |
|---|---|---|---|---|---|
| **partial** κ=0.5 η=0.25 | 180 | 0.3585 | **+0.5911** | **0.759** | 1.351 |
| naive κ=1.0 η=0.0 | 180 | 0.3750 | +0.5697 | 0.731 | 1.335 |

NAV / drawdown (same window):

| config | cum return | annualized | max DD | avg gross w |
|---|---|---|---|---|
| partial | +120.9% | +21.9% | -37.9% | 0.488 |
| naive | +112.4% | +20.7% | -38.9% | 0.489 |

Turnover sweep (κ × η) — Sharpe vs turnover curve:

| κ | η | turnover | Sharpe | mean net R |
|---|---|---|---|---|
| 0.25 | 0.00 | 0.3578 | 0.777 | +0.6100 |
| 0.25 | 0.25 | 0.3559 | 0.772 | +0.6049 |
| 0.50 | 0.00 | 0.3629 | 0.762 | +0.5962 |
| **0.50** | **0.25** | **0.3585** | **0.759** | **+0.5911** |
| 0.50 | 0.50 | 0.3548 | 0.758 | +0.5899 |
| 1.00 | 0.00 | 0.3750 | 0.731 | +0.5697 |
| 1.00 | 0.50 | 0.3593 | 0.737 | +0.5710 |

The partial-rebalance thesis is **directionally confirmed but modest**: partial
(κ=0.5, η=0.25) cuts turnover 0.375 → 0.359 (~4%), lifts net edge +0.5697 →
+0.5911 R, Sharpe 0.731 → 0.759, and annualizes +21.9% vs +20.7%. The benefit is
small because weekly turnover is dominated by **quintile membership changes**
(which trade full by design, §2.2) rather than in-leg drift — the κ/η knobs only
act on drift.

## (c) G3 verdict (xsmom_g3_record, shipping config κ=0.5 η=0.25) — REAL

| metric | value | gate | result |
|---|---|---|---|
| n | 180 | ≥ 10 | PASS |
| optimistic mean R (zero cost) | +0.6341 | — | (diagnostic) |
| realistic mean R (net of 12 bps) | **+0.5911** | > 0 | PASS |
| pessimistic PF (extra worst-fill taker leg) | **1.3401** | > 1.0 | PASS |
| edge decay (realistic/optimistic) | 0.9322 | ≥ 0.60 | PASS |

**Cost-aware construction SURVIVES G3 realistic fills** (net edge > 0). The
12-bps round-trip is applied exactly once (F10) and does not kill the edge.

## (d) CPCV (N=12, k=2) + DSR/PBO — REAL, FAILS overfit controls

| control | value | threshold | result |
|---|---|---|---|
| split PF median | 1.351 | ≥ 1.3 | PASS |
| split PF 10th-pct | **0.723** | ≥ 1.0 | **FAIL** |
| split PF min | 0.377 | — | (weak tail) |
| PBO | **0.561** | < 0.30 | **FAIL** |
| DSR | **0.663** | > 0.95 | **FAIL** |
| agg split Sharpe | 0.105 | — | (weak OOS) |

## (e) Regime + beta-cluster partition — REAL

| regime | n | mean net R | PF |
|---|---|---|---|
| overlay up (BTC > 200-DMA) | 113 | +0.7529 | 1.407 |
| overlay down | 67 | +0.3182 | 1.227 |
| bull (BTC 30d > +2%) | 91 | +1.3874 | 1.819 |
| bear (BTC 30d < -2%) | 63 | -0.1657 | 0.890 |
| neutral | 26 | -0.3624 | 0.825 |

The edge is **concentrated in BTC bull regimes**: bull episodes contribute a
+1.39 R mean and PF 1.82, while bear (−0.17 R, PF 0.89) and neutral (−0.36 R,
PF 0.83) are flat-to-negative. Per-name rolling 30d BTC betas are almost all
≥ +1.3 (ENA +3.0, NEAR +2.9, OP +2.7 …), with only HYPE (+0.28) and TRX (−0.41)
below the "high-beta" line — this is a **directional beta book**, not a
market-neutral spread (consistent with the F1 LONG-FLAT resolution).

## Verdict (honest)

1. **Net edge (R / period), partial vs naive:** +0.5911 vs +0.5697 mean net R;
   Sharpe 0.759 vs 0.731; annualized +21.9% vs +20.7%. Partial rebalance
   **beats** full turnover — the core US-182 thesis holds on this data.
2. **G3 clear:** YES — realistic mean R +0.5911 > 0 and pessimistic PF 1.34 > 1.0
   through the internal 12-bps cost model (counted once). The cost-aware
   construction survives realistic fills.
3. **But it is NOT a robust, promotable alpha.** The edge fails the PROP-001
   overfit controls: CPCV 10th-pct split PF 0.72 < 1.0 (G4), PBO 0.56 > 0.30 and
   DSR 0.66 < 0.95 (G5); and the P&L is a Bitcoin-trend beta artifact — bull
   regimes carry all of it, bear/neutral are non-positive. The pre-registered
   G3 falsifiers (a–d) do **not** trip, so this is not a G3 demotion; but per the
   gauntlet it gets **NO PROMOTION** and stays a **Hypothesis** (paper): the
   apparent 22%/yr is directional crypto beta with a regime overlay, not a
   transaction-cost-defeating cross-sectional edge that generalizes out-of-sample.

No paper-forward deferral was requested or performed; the deep daily data is
complete and same-venue, so this is a genuine in-sample verdict, not an
"insufficient data" punt.