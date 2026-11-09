---
topic: general
confidence: high
has_quotes: true
tags: []
source: HermesForge Strategies
created: 2026-11-09
---
# HYP-34 — Order-flow imbalance (CVD) — phase 1a

**Verdict: NOT a taker edge. Positive gross, negative net after cost — exactly the prior.**
**Confidence: medium on the verdict for the *liquidation-flow* proxy; the FULL order-flow question is UNMEASURED (data absent).**

## Data reality (read first — this bounds everything)

The hypothesis's primary signal is **full order-flow CVD** — cumulative aggressive-buy
minus aggressive-sell notional across *all* tick trades. The full tick-trades dataset
(`~/.hermes/market_data (ironflow/hyperliquid-trades)`, 5.8GB daily files) referenced in
the data_dependencies is **NOT on disk**. Exhaustive search (`find /` for >3GB files,
>100MB parquet, `ironflow`/`hyperliquid-trades`/`trades` dirs and names) found no such
dataset. The ONLY aggressor-side tick source present is the **liquidation fills** store
(`hl_liquidations_hf/data/fills/*.parquet`, 18 months, 2025-05-25 → 2026-10-31, ~8.1M
fills).

A liquidation is a *forced taker* order, so its `side` IS an aggressor direction
(short-liq → aggressive buy; long-liq → aggressive sell). This driver therefore computes
a **liquidation-flow CVD** — the *forced-flow subset* of CVD — as the closest available
proxy. It is a real, well-defined signal, but it is **not** full order-flow CVD. The full
question stays open: full aggressive flow could carry a materially stronger (or different)
relationship.

This is a data-availability boundary, not a tuning choice. The `full_trades_absent: true`
flag is hashed into every trial.

## Pre-registered operationalization (fixed)

- Signal: `CVD level C[t] = cumsum(buy − sell notional)` and its short-window change
  `D[t] = C[t] − C[t−K]`. Tradable rule = `sign(D[t])` → same-direction continuation.
- Intraday (BTC only; ETH/SOL 5m bars begin 2026-10-15 → <16d overlap, ineligible, same
  constraint as HYP-27): K = 12 bars (1h); horizons h ∈ {1, 6, 12} bars = 5m/30m/1h;
  entry = bar-t close. Window 2026-06-15 → 2026-10-31 (~4.5 months).
- Daily (BTC + ETH pooled, full 18 months): K ∈ {1d, 3d}; horizon 1d; daily marks from
  crypto/BTC.parquet + crypto/ETH.parquet (validated: mean |Δ| 0.017% vs 5m-bar close).
- Cost: taker round-trip 11.5bps intraday / 12bps 1d (4.5bps taker ×2 + 2.5bps adverse
  slip [+ 0.5bps funding 1d]); maker round-trip 3bps (1.5bps ×2, no spread credited);
  G0 fail-closed hurdle 45bps gross/leg. No leverage. LIVE off.
- Arms: H1 continuation (taker), H2 reversal (maker-side capture, = −H1 gross by
  construction).

## Results

### Intraday BTC (5m CVD)

| horizon | corr(cvd_level, fwd) | corr(roc, fwd) | H1 taker gross | H1 taker net | H2 maker net |
|---|---|---|---|---|---|
| 5m   | −0.0005 | +0.0175 | −0.11 bps | −11.61 bps | −2.89 bps |
| 30m  | −0.0013 | +0.0375 | +0.29 bps | −11.21 bps | −3.29 bps |
| 60m  | −0.0022 | +0.0327 | +0.34 bps | −11.16 bps | −3.34 bps |

- **CVD level is not predictive** (~0 correlation): the running cumsum is contaminated by
  structural drift (liquidation sells dominate ~62:38 over the window). Only the
  **rate-of-change** carries signal — and it is weak.
- **Continuation is real but tiny**: `corr(roc, fwd)` peaks at +0.04 (30m), gross peak
  +0.34bps (1h). t-stats (declustered) all |t| < 1.0 — insignificant.
- **Gross ≪ taker cost everywhere**: +0.34bps peak vs 11.5bps round-trip. Net is
  uniformly −11.2 to −11.6bps. G0 (45bps) fails hard.

### Daily BTC+ETH (full 18 months)

| trailing K | corr(roc, 1d fwd) | H1 taker gross | H1 taker net | H2 maker gross | H2 maker net |
|---|---|---|---|---|---|
| 1d | +0.0249 | +5.17 bps | −6.83 bps | −5.17 bps | −8.17 bps |
| 3d | +0.0002 | −1.62 bps | −13.62 bps | +1.62 bps | −1.38 bps |

- K=1d gross +5.17bps is the strongest cell, but still < half the 12bps taker round-trip,
  t +0.60 (insignificant), win 0.502.
- K=3d ("sustained") reverse to a slightly negative gross (−1.6bps) — the multi-day
  running flow is information-neutral.
- **Maker-side (H2) survives nowhere**: reversal gross is +0.1 to +1.6bps, far below even
  the 3bps maker fee. The forced flow does not mean-revert enough to pay a maker.

## Honest verdict

1. **Sign**: weak positive same-direction continuation (roc → +fwd), consistent with
   liquidation *cascade* momentum at 30m–1h, not mean-reversion.
2. **Magnitude**: sub-basis-point to a few bps gross; the signal is real but economically
   marginal even before cost.
3. **Net**: negative after realistic taker cost at every horizon; negative even for the
   maker-side (reversal) arm at 3bps. **No cell clears the 45bps G0 hurdle.**
4. **Bottom line**: as measured here, order-flow imbalance is **the market-maker's edge,
   not a taker's** — positive gross / negative net, exactly as prior expected. The maker
   who absorbs forced liquidation flow is *not* clearly being paid here either (H2 net
   negative at a conservative 3bps), which itself says the forced-flow CVd is close to
   information-neutral at these horizons.

## Open items

- **Full order-flow CVD remains untested** for lack of the 5.8GB trades dataset. If it is
  ever backfilled, re-run with the identical driver against true aggressive buy/sell to
  settle the hypothesis's actual target. Until then HYP-34 is **falsified only for the
  forced-flow proxy**, not for full CVD.
- Decile/quantile conditioning on |D| (magnitude, not just sign) was intentionally left
  out of phase 1a to preserve pre-registration; a magnitude-conditioned version is a
  separate, low-priority follow-on.

Driver: `scripts/gauntlet/backtest_hyp34_order_flow_cvd.py` (10 trials written, fresh
param_hash each; ledger integrity OK).