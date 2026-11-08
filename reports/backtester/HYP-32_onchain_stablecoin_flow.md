---
hypothesis_id: HYP-32
backtester: hermes-forge (backtester)
status: FALSIFIED (coincident echo, not a leading flow signal)
date: 2026-11-08
data: DefiLlama free API backfill (aggregate stablecoin supply + aggregate TVL, 2017→2026) + daily BTC/ETH close, 2020-08-19 → 2026-11-08
param_hash: 1a496ef10755b011
---

# HYP-32 — On-chain / stablecoin + TVL flow → subsequent price: verdict

First test of the untested on-chain/macro-flow data class. The pre-registered
prior was "likely null — flow is correlated WITH price, not causal/leading."
That prior is confirmed, with the exact failure mode it flagged: **coincident
echo, not lead.**

## Executive verdict

**NOT PROMOTED. No tradeable leading edge.** Aggregate stablecoin supply growth
and aggregate TVL growth are strongly coincident with price (they rise together
in a bull market) and do NOT predict forward return at a tradeable weekly
horizon. Three independent kills:

1. **The lead-lag correlogram peaks at NEGATIVE lag.** For every one of the 8
   cells (2 coins × 2 flow types × 7d/30d), the largest |correlation| between
   flow growth and daily return sits at h = −4 … −29 days — i.e. flow *lags*
   price, it does not lead it. At h=0 and all forward lags (h>0) the correlation
   collapses to near-zero. (See §1.)
2. **Echo ≫ forward everywhere.** The echo IC (flow at t vs the *trailing*
   week's return) is large and highly significant (up to +0.74, t≈19 for ETH
   TVL 7d), while the forward IC (flow at t vs the *next* week's return) is
   near-zero in 7 of 8 cells. (See §2.)
3. **The sign strategy's returns are pure long-beta.** A long-when-growth>0
   signal is long ~55–70% of the time in a 6.2-year window where BTC is +546%
   and ETH is +450%. Every cell *underperforms* buy-and-hold (negative excess
   CAGR), except one borderline case that still fails the load-bearing
   lead-vs-echo test. (See §2, §3.)

---

## 1. Lead-lag structure (the honesty test)

Cross-correlation corr(flow_growth_t, daily_log_return_{t+h}). h<0 = flow LAGS
price (echo); h=0 = coincident; h>0 = flow LEADS.

```
                    peak|corr|        corr at selected lags
signal             lag          h=-7     h=-1    h=0     h=+1    h=+7
BTC supply 7d      -7   (+0.12)  +0.124  +0.058  +0.027  +0.015  +0.013
BTC supply 30d     -29  (+0.08)  +0.039  +0.015  +0.007  +0.004  +0.017
BTC tvl    7d      -6   (+0.31)  +0.295  +0.260  +0.030  -0.009  +0.007
BTC tvl    30d     -29  (+0.17)  +0.113  +0.106  +0.016  +0.013  +0.023
ETH supply 7d      -7   (+0.12)  +0.121  +0.072  +0.048  +0.040  +0.031
ETH supply 30d     -27  (+0.09)  +0.061  +0.042  +0.034  +0.033  +0.037
ETH tvl    7d      -4   (+0.34)  +0.317  +0.291  +0.035  -0.010  +0.020
ETH tvl    30d     -29  (+0.17)  +0.147  +0.152  +0.052  +0.044  +0.053
```

The pattern is identical across all 8 cells: correlation is largest at the most
negative lags, decays as h→0, and flattens to ~0 at h≥0. This is the textbook
signature of a **lagging/coincident echo** — flow moves *with or after* price,
never before it. There is no positive forward-lag structure to trade.

---

## 2. Weekly (non-overlapping) IC: forward vs echo

1. forward IC = corr(growth_t, forward return t→t+7) — the **tradeable
   leading** measure.
2. echo IC = corr(growth_t, trailing return t−7→t) — does flow merely echo the
   price move it moved with?
3. Granger = coef on growth in fwd_ret ~ growth + trailing_ret + trailing_growth
   (does flow add anything once you know what price just did?).

```
signal           fwd IC  (p)       echo IC (p)       Granger t(g)
BTC supply 7d    +0.051  (0.357)   +0.188  (0.001)   +2.08
BTC supply 30d   +0.019  (0.733)   +0.052  (0.349)   -1.16
BTC tvl    7d    +0.006  (0.910)   +0.631  (<1e-4)   -0.45
BTC tvl    30d   +0.063  (0.261)   +0.260  (<1e-4)   +1.06
ETH supply 7d    +0.091  (0.103)   +0.197  (<1e-4)   +1.88
ETH supply 30d   +0.083  (0.133)   +0.116  (0.036)   +0.51
ETH tvl    7d    +0.004  (0.937)   +0.736  (<1e-4)   +0.54
ETH tvl    30d   +0.151  (0.006)   +0.370  (<1e-4)   +2.95
```

The echo IC is uniformly large and significant; the forward IC is uniformly
small. The one cell with a nominally significant forward IC (ETH/tvl-30d,
fwd +0.151, raw p=0.006) has an echo IC (+0.37) that is 2.4× its forward IC —
it is far more "what price just did" than "what price will do next."

---

## 3. Traded P&L net of cost (weekly rebalance, long-when-growth>0, else flat)

Cost = 12 bps round-trip on each flip + 0.5 bps/week funding (fee_source crypto
model, no maker rebate). Benchmarked against buy-and-hold (B&H) over the same
window. BTC B&H +546% (CAGR +35.0%/yr); ETH B&H +450% (CAGR +31.5%/yr).

```
signal        net total  CAGR      Sharpe   vs B&H (excess CAGR)
BTC supply 7d  +215.7%   +25.0%/yr  0.70    −10.0%/yr
BTC supply 30d +196.5%   +22.5%/yr  0.66    −12.5%/yr
BTC tvl    7d  +49.4%    −2.1%/yr   0.21    −37.0%/yr
BTC tvl    30d +184.9%   +22.4%/yr  0.68    −12.6%/yr
ETH supply 7d  +285.4%   +26.0%/yr  0.69    −5.5%/yr
ETH supply 30d +223.4%   +15.4%/yr  0.55    −16.1%/yr
ETH tvl    7d  +79.9%    −6.6%/yr   0.21    −38.1%/yr
ETH tvl    30d +351.4%   +46.1%/yr  0.93    +14.6%/yr
```

Seven of eight cells *lose* to buy-and-hold after cost (the strategy is simply
an intermittent long in a strong bull market). The one exception (ETH/tvl-30d,
+14.6%/yr excess) is examined below and fails the lead-vs-echo test.

(Note: a plain weekly momentum benchmark — does *this* week's return predict the
next? — is ≈ 0: BTC −0.023, ETH −0.049. So the ETH/tvl-30d excess is not weekly
momentum; it is the *slow* TVL 30-day trend acting as a coarse trend filter.)

---

## 4. The single borderline cell (ETH/tvl-30d), examined honestly

ETH/tvl-30d is the only cell with (a) a marginally-significant forward IC
(+0.151, raw p=0.006, Bonferroni p=0.049 over 8 cells), (b) positive excess over
B&H (+14.6%/yr), and (c) a Granger t of +2.95. It is NOT promoted because:

1. **It fails the load-bearing lead-vs-echo test.** Its echo IC (+0.37) is 2.4×
   its forward IC (+0.15). By the hypothesis's own definition — "leading not
   coincident (flow at t predicts return t+1, not just correlates with return
   t)" — a signal that is 2.4× more an echo than a lead is *coincident*, not
   leading.
2. **It is 1 of 8 cells.** Bonferroni-adjusted p = 0.049 is marginal, and the
   two "coins" are not independent tests (both share the single aggregate flow
   series), so the effective multiplicity is higher than the nominal 8.
3. **It is mechanistically a trend filter, not a flow lead.** TVL's 30-day
   growth is a slow, autocorrelated series that is high exactly during the
   sustained up-trends of the 2020→2026 bull. Being long when it is high is
   crude trend-following on a coincident macro proxy — the same phenomenon the
   echo IC already captures — not an independent causal signal that mints before
   price bids.

This is reported honestly and NOT promoted, per the hypothesis's falsification
conditions.

---

## 5. Verdict

On-chain/macro flow (aggregate stablecoin supply + aggregate TVL) does **not**
lead price at a tradeable weekly horizon. It is a **coincident echo** — it rises
and falls *with* price, peaks at negative lag in the correlogram, has large
echo IC and near-zero forward IC, and produces no alpha over buy-and-hold in 7
of 8 cells (the one borderline cell fails the lead-vs-echo test and multiple
testing). The result matches the pre-registered prior exactly.

**Implication for future work:** if a genuine *leading* on-chain signal exists,
it will not be at the aggregate macro level. Per-coin (exchange netflows,
whale/inflow concentration) is the natural next probe — but that is paid tier
(Glassnode/CryptoQuant), flagged in the hypothesis note as a follow-up only if
justified. The aggregate flow hypothesis is now falsified and should not be
re-tested with tuning.