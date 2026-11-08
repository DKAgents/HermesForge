---
hypothesis_id: HYP-33
backtester: hermes-forge (backtester)
status: DATA-GATED (free long/short-ratio reach < 1yr; H2 top-trader reach ~3.3mo)
date: 2026-11-08
data: OKX public rubik endpoints (live probe, no fabrication)
venue: okx (long/short ratio) — price leg NOT evaluated (gate failed first)
---

# HYP-33 — Crowd long/short ratio (contrarian positioning): DATA-GATED verdict

VERDICT: DATA-GATED — neither H1 nor H2 was run. The free OKX rubik
long/short-ratio history does not reach the >=1yr bar required for a meaningful
daily/weekly contrarian-positioning backtest. No history was fabricated, no
price was proxied, nothing was tuned (nothing ran, so G5 is intact).

---

## 1. Data reach (probed live, not assumed)

Three pre-registered signals were probed directly against OKX public rubik:

| endpoint (period=1D)                          | result        | reach (UTC)                        |
|-----------------------------------------------|---------------|------------------------------------|
| `long-short-account-ratio?ccy=BTC`            | 180 points    | 2026-05-13 -> 2026-11-08 (~6.0 mo) |
| `long-short-account-ratio?ccy=ETH`            | 180 points    | 2026-05-13 -> 2026-11-08 (~6.0 mo) |
| `...-contract-top-trader?instId=BTC-USDT-SWAP`| 100 points    | 2026-08-01 -> 2026-11-08 (~3.3 mo) |
| `...-contract-top-trader?instId=ETH-USDT-SWAP`| 100 points    | 2026-08-01 -> 2026-11-08 (~3.3 mo) |
| `taker-long-short-ratio`                      | HTTP 404      | endpoint unavailable               |

Pagination probes (`before=`, `after=`, `begin`/`end`) all return the same
fixed window or `Illegal time range` (50030) — the free history is hard-capped,
not merely default-truncated. No query extends it past 180 points.

---

## 2. Which signal is testable, and at what N

The requirement (per the hypothesis + run brief) is >=1yr of daily history for a
daily/weekly backtest with a meaningful extreme-decile sample. The reality:

- **H1 (retail account-ratio fade)** — the *most* reach is ~6.0 months = ~180
  daily bars. Extreme decile (10%) => ~18 daily signals, or ~8 weekly
  (non-overlapping) bars at a weekly rebalance. This is far too small to claim
  a robust contrarian edge on a "partly arbitraged" signal that the hypothesis
  already assigns low-medium confidence.
- **H2 (top-trader divergence)** — ~3.3 months = 100 bars => ~10 extreme-decile
  signals. Effectively untestable at any tradeable horizon.
- **Taker ratio** — not served by the free endpoint at all.

Both legs fail the >=1yr gate. The retail leg is 1.8x under the bar; the
top-trader leg (which H2 depends on) is ~3.6x under it.

---

## 3. Why not test on the available window anyway

The run brief is explicit: "If free reach is only ~3 months (or otherwise too
short for a daily/weekly backtest with meaningful sample), REPORT DATA-GATED
and STOP — do NOT test on an inadequate window." Testing ~18 (or ~10) extreme
events would produce a result that is statistically meaningless — and the
hypothesis's falsification/promotion criterion ("net-positive, leading, AND
robust") cannot be demonstrated on such N. Running it would manufacture a
confident-looking number from noise; that is worse than reporting the gate.

---

## 4. Honest path forward (no fabrication)

1. **Forward accumulation** — a listener appending the daily account-ratio (and
   top-trader) series would clear the 1yr bar around mid/late 2027. This is the
   zero-fabrication path; HYP-33 re-opens automatically once reach >=1yr.
2. **Paid / alternate history** — OKX does not serve deep free rubik history.
   A vendor archive (Glassnode/CryptoQuant positioning data) would be a *different
   data source*, not a re-run of the registered OKX-ratio test; it would need its
   own pre-registration before use.
3. **Taker ratio** — dead end on this free endpoint; flag as unavailable, do not
   substitute.

No trial was written to data/gauntlet/trials.jsonl: a data gate is a STOP before
any backtest, and a synthetic trial row (invented avg_r/pf/pbo) would itself be a
data-fabrication / G5 violation. There is no result to log; there is no param_hash
because no experiment was constructed.

---

## 5. Verdict

Crowd long/short-ratio positioning (HYP-33) is **untested, not rejected.** The
contrarian-positioning mechanism remains coherent and is a genuinely different
axis from OI *level* — but it is currently unverifiable because the free OKX
ratio history does not reach one year (6.0 months retail, 3.3 months top-trader,
taker unavailable). This matches the hypothesis's own pre-registered data-gate
warning. Report data-gated; do not promote; do not re-test with tuning.