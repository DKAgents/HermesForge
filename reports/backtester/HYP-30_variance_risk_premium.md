---
hypothesis_id: HYP-30
backtester: hermes-forge (backtester)
status: FALSIFIED (not harvestable as pre-registered)
date: 2026-11-07
data: Deribit options-history backfill (US-231) + DVOL store (US-187), 2024-11-07 → 2026-11-07
param_hash: 9c63e93feea2fa30
---

# HYP-30 — Variance Risk Premium: verdict

SELL ATM straddles (BTC/ETH), hold to expiry, gated on vol-of-vol timing. This
is the honest read of the pre-registered signal — the tail, not the mean, is
the question, and the tail answers it.

## Executive verdict

**NOT HARVESTABLE. Falsified as pre-registered.** Three independent kills:

1. **The vol-of-vol gate is empirically BACKWARDS.** The pre-registered rule
   ("enter only in low/decaying DVOL") selects the *worst* regime and excludes
   the *only* regime that nets positive. The harvestable premium sits in
   ELEVATED vol, not calm vol — on both BTC and ETH.
2. **A single vol spike gives back more than a year of premium.** BTC worst
   trade −17.5% of notional in one week vs ~+15.7%/yr ungated maker — one week
   erases >1yr of the (optimistic, maker-only, ungated) carry.
3. **ETH is negative in every configuration** (unconditional, gated, maker,
   taker, weekly, monthly). The "VRP is the second risk premia" prior does not
   hold on the ETH leg or survive cost/tail on the BTC leg.

---

## 1. VRP (implied − realized, vol points) per currency per year

Primary horizon = weekly straddles held to expiry (the store's venue cadence;
105 trades/coin over ~2y). Monthly (30d, 24 trades) reported as robustness.

```
                BTC                     ETH
  horizon   ungated  gated         ungated    gated
  weekly     +2.32    +2.61          -0.79     -4.01
  monthly    +0.12    -2.67          -5.18    -12.25
```

By year (weekly, ungated / gated):

```
  BTC   2024 +7.45 (n=8)  2025 +3.11 (n=52)  2026 +0.50 (n=45)
  ETH   2024 +3.28 (n=8)  2025 -2.76 (n=52)  2026 +0.77 (n=45)
```

The backfill's own honest flag was "+2.63pp BTC, −3.13pp ETH". Reproduced:
BTC weekly +2.32 (ungated) / +2.61 (gated) ≈ +2.63; ETH weekly −0.79, monthly
−5.18, bracketing −3.13. Direction is robust: BTC thin-positive, ETH negative.

Two structural warnings already visible here:

- **The BTC premium is a WEEKLY phenomenon, not a robust one.** +2.3pp at 7d
  collapses to +0.1pp at 30d. Short-dated (retail-speculation-rich) BTC gamma
  is where the premium sits; there is no persistent structural VRP beyond it.
- **The premium is DECAYING.** BTC +7.45 → +3.11 → +0.50pp by year. Whatever
  short-dated premium existed is compressing toward zero (the same decay family
  that killed the momentum edges).

---

## 2. Net straddle P&L after spread + margin (bps of notional)

Charged on BOTH legs: option bid-ask spread (vol points — flagged assumption,
no L2 options book held) + taker fee 3bps×2 legs + margin opportunity cost
(premium + 20% underlying, 5%/yr). Maker = fill at mark, no rebate. Taker =
cross half a 2-vol-pt spread. Taker+stress = half a 4-vol-pt spread.

```
  BTC  maker       +3,125 bps total  (+1,567/yr ungated, +235/yr gated)   sharpe 0.46
       taker       +1,308 bps        (  +656/yr ungated, -277/yr gated)   sharpe 0.19
       taker+stress  +120 bps        (   +60/yr ungated, -611/yr gated)   sharpe 0.02

  ETH  maker       -1,542 bps        (  -773/yr ungated, -4,857/yr gated) sharpe -0.16
       taker       -3,360 bps        (-1,685/yr ungated, -5,326/yr gated) sharpe -0.35
       taker+stress-4,548 bps        (-2,280/yr ungated, -5,632/yr gated) sharpe -0.48
```

The decisive structure:

- **The GATE destroys the edge.** BTC ungated maker +1,567 bps/yr → gated +235
  bps/yr; taker flips to *negative* (−277/yr) once gated. The pre-registered
  filter routes the strategy away from its own source of profit.
- **Only the ungated, maker-only, optimistic path is positive on BTC** — and it
  is not the pre-registered strategy (which gates), and it still does not
  survive the tail (below).
- **ETH is negative everywhere.** No config clears.
- **Sharpe ≤ 0.46 even on the best cell** — statistically indistinguishable from
  zero (n=105, ~52/yr). No G4 significance, no G5 DSR, even before the tail.

---

## 3. The tail — the honest unknown

Weekly hold-to-expiry, coin-settled P&L (no early-exit rescue; a spike mid-hold
is eaten in full at settlement).

```
  max drawdown (equity curve)      worst single trade
  BTC  -80.8% (maker) / -106.9% (taker) / -139.8% (stress)
       -1,747 bps taker  = -17.5% of notional in one week  (2026-05-28)
  ETH  -323.7% (maker) / -395.0% (taker) / -449.1% (stress)
       -3,017 bps taker  = -30.2% of notional in one week  (2026-01-29)
```

The worst BTC trade is a real event, not a data artifact: Bitcoin fell ~73.4k →
~61.0k (≈ −17%) over the 2026-05-28 → 06-04 week. A short straddle struck at
73k with ~3.4% premium collected settles to |S−K|/S ≈ 19.6% → −16%+ net.

**Does a single vol spike give back a year of premium? YES.**

- BTC: worst week −1,747 bps vs ungated maker +1,567/yr. **One week > one year.**
  Under taker, worst week −1,747 bps vs +656/yr ≈ 2.7 years.
- ETH: worst week −3,017 bps is larger than any annual figure it could collect.

Vol-spike episodes through the trade window (DVOL ≥ +20%/7d), and the net P&L
of straddles held through each — every one NET-NEGATIVE, none rescued by the gate:

```
  BTC  2026-01-27→02-01  DVOL 38→48 (+26%)  2 held  net -1,787 bps (taker)
       2026-05-26→06-02  DVOL 36→43 (+21%)  2 held  net -2,049 bps (taker)
       2026-08-14→08-19  DVOL 35→38 (+9%)   2 held  net -1,552 bps (taker)
  ETH  2026-01-27→02-01  DVOL 54→66 (+22%)  2 held  net -3,378 bps (taker)
       2026-05-27→06-02  DVOL 49→56 (+13%)  2 held  net -2,422 bps (taker)
       2026-08-16→08-19  DVOL 47→53 (+11%)  1 held  net -2,029 bps (taker)
```

The tail is not a rare-one-off: it is the recurring, load-bearing, uncompensated
exposure of this trade, and it is larger than the edge it protects.

---

## 4. Why the mean and the tail co-locate (the gate is backwards)

The conditional matrix — net-R by entry-DVOL percentile (trailing 90d) — is the
smoking gun:

```
  BTC                                                        ETH
  DVOL pct   VRP      net-R maker/taker                      DVOL pct   VRP      net-R maker/taker
  0.00-0.04  +1.5pp   -0.070 / -0.113                        0.00-0.13  -10.9pp  -0.899 / -0.929
  0.06-0.17  +1.9pp   -0.173 / -0.215                        0.14-0.36  -8.9pp   -0.275 / -0.301
  0.20-0.52  -3.1pp   -0.255 / -0.294                        0.37-0.60  +4.1pp   +0.171 / +0.146
  0.53-0.81  +6.3pp   +0.311 / +0.277   <- positive          0.61-0.77  -5.3pp   +0.350 / +0.327   <- positive
  0.82-1.00  +5.0pp   +0.202 / +0.173   <- positive          0.81-1.00  +16.2pp  +0.326 / +0.304   <- positive
```

Net-R turns positive **only in ELEVATED/SPIKING DVOL**, and is negative in the
calm/low-DVOL regime the pre-registered gate selects. On ETH the low-DVOL
regime is the *worst* (−0.90 maker) — ETH still jumps when DVOL is low, so
selling "cheap" calm ETH vol loses. The premium (implied > realized) is richest
exactly where the tail lives; there is no way to pick up the mean without
picking up the spike.

This is the exact inverse of the skill's "vol-of-vol timing" thesis for this
asset/window. The honest reading: **crypto's short-vol premium is a
short-the-spike carry** — you are paid for holding a spike you cannot dodge.
The calm-regime "harvest" the gate was built to capture does not exist.

---

## Verdict vs the gates, and diversification

- **G0 (cost-first):** fails. The gross (BTC +2.3pp) does not clear cost+tail at
  any honest fill tier; the only positive cell is ungated maker, which is not
  the pre-registered strategy and still carries a −80% drawdown.
- **G4 (CPCV) / G5 (DSR/PBO):** fails by construction — Sharpe ≤0.46 on the best
  cell, negative on ETH; a decaying, tail-dominated, single-regime premium has
  no out-of-sample stability to find. (No parameter was tuned; the failure is
  signal-absence + a backwards gate, not overfit.)
- **Tail:** fails — one week ≥ one year of premium. The "mean is positive" prior
  is confirmed (thinly, BTC weekly, decaying) but the load-bearing question is
  the tail, and it says no.

**Is it diversifying against the funding carry? No — it is the carry's left
tail, re-sold.** Both are short-risk-premia that earn in calm/flats and lose in
the same risk-off vol spike: carry loses when funding flips negative (panic),
VRP loses directly when vol spikes. They diversify in the *body* (their
daily returns are largely uncorrelated) but **concentrate in the tail** — which
is precisely the wrong kind of diversification for a short-vol book. Adding VRP
to the carry does not hedge the carry's tail; it doubles it.

## Disposition

Retire HYP-30 as pre-registered. No paper-forward, no paper, no promotion. The
one residual question worth a *future* exploration (only if the user asks, and
only as a pre-registered NEW hypothesis) is "sell vol only on confirmed
DECAYING-from-elevated DVOL on BTC weeklies with a hard vol-spike stop" — the
conditional matrix shows net-R positive in the 0.53+ DVOL band, and a spike stop
(exit when DVOL gaps further) is the only thing that could separate that mean
from its tail. That is a different, harder, currently-untested strategy — not
HYP-30, and not a reason to keep the pre-registered product alive.

## Method / provenance notes (no silent assumptions)

- Data: US-231 options-history backfill (Deribit mark prices, coin-settled);
  US-187 DVOL. Window 2024-11-07 → 2026-11-07 (~2y, 105 weekly expiries/coin).
- Premium = `atm_straddle_premium` (BTC per 1-coin contract); payoff = |S−K|/S_T
  (coin-settled/reversed). Identity verified: premium/S0 ≈ 0.798·σ·√T within ~1%.
- Realized vol over the hold = annualized std of daily log-returns, entry→expiry.
- No look-ahead: entry on close-only info; gate on trailing (prior-day) DVOL mean.
- No leverage; cost on both legs; live OFF; fresh param_hash → trials ledger
  (156th trial; chain verified).
- Flagged assumptions: S_T is the expiry-day daily close (proxy for 08:00 UTC
  index settle); option bid-ask spread is a vol-point band (no L2 book held);
  margin opportunity 5%/yr. Intra-hold mark-to-market drawdown was NOT fabricated
  (the store re-strikes to ATM each day, so my fixed-strike straddle cannot be
  marked cleanly) — the settled terminal P&L is the honest worst case.
