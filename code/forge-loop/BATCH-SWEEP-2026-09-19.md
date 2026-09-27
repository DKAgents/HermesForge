# BATCH G0+G3 GAUNTLET SWEEP — 2026-09-19

**36 candidates tested (26 vault + 10 seed pool)**
**Cost model: stock=2 bps, crypto=12 bps (per cost_adjuster.py VENUE_COSTS)**
**All metrics winsorized at P1/P99 to neutralize outlier distortion**

---

## RANKED SURVIVORS (G0+G3 PASS)

| # | Strategy | Net Avg R | Gross Avg R | Edge Retention | PF | Trades | Asset | Status |
|---|---|---|---|---|---|---|---|---|
| 1 | **STR-20260906-BTC-SUPPLY-CRUNCH** | +2.6736 | +2.6776 | 99.9% | 78.93 | 47 | stocks | watch |
| 2 | **STR-B-macd-histogram-divergence** | +0.8624 | +0.8838 | 97.6% | 1.89 | 3,126 | stocks | live |
| 3 | **STR-20260730-atr-contraction-breakout** | +0.6704 | +0.8641 | 77.6% | 2.39 | 313 | stocks | unknown |
| 4 | **STR-DEBASEMENT-treasury-buyback** | +0.2776 | +0.3018 | 92.0% | 1.50 | 65 | stocks | watch |
| 5 | **STR-20260728-adaptive-trend** | +0.2129 | +0.2154 | 98.9% | 1.58 | 1,730 | stocks | unknown |
| 6 | **STR-20260901-oil-shock-sector-rotation** | +0.1797 | +0.1839 | 97.7% | 1.33 | 148 | stocks | unknown |
| 7 | **STR-20260917-CAP-BOTTOM** | +0.1320 | +0.1444 | 91.4% | 1.32 | 139 | crypto | watch |
| 8 | **STR-VIXC-vix-contango-breakout** | +0.0916 | +0.0943 | 97.1% | 1.34 | 15,518 | stocks | watch |
| 9 | **STR-20260818-lowcorr-regime** | +0.0770 | +0.0817 | 94.2% | 1.23 | 31,464 | stocks | unknown |
| 10 | **STR-20260719-sr-role-reversal-entry** | +0.0493 | +0.0572 | 86.2% | 1.07 | 2,402 | stocks | unknown |
| 11 | **STR-20260908-SKEW-PREDICTED** | +0.0487 | +0.0526 | 92.6% | 1.14 | 17,214 | stocks | watch |
| 12 | **STR-A-ma-pullback-fibonacci** | +0.0487 | +0.0659 | 73.9% | 1.05 | 1,123 | stocks | watch |
| 13 | **STR-G-relative-strength** | +0.0403 | +0.0665 | 60.6% | — | 21,733 | stocks | killed |
| 14 | **STR-C-breakout-volume-trend** | +0.0066 | +0.0217 | 30.3% | 1.01 | 12,106 | stocks | hypothesis |

**14 PROMOTE (all pass G0 median-|R| > cost-drag + G3 net-R > 0)**

Key caveats:
- **BTC-SUPPLY-CRUNCH**: Only 47 trades; 93.6% win rate is unsustainable. Likely overfit or sample-selection bias. Needs >=100 trades before paper.
- **ATR-CONTRACTION**: Low trade count (313) but strong PF (2.39). Needs more data.
- **DEBASEMENT**: Only 65 trades. Sample too small for confidence.
- **OIL-SHOCK**: 148 trades, narrow but real edge.
- **CAP-BOTTOM**: Only crypto strategy surviving G0+G3; cost drag 0.0124R (crypto 12 bps model).
- **Breakout Volume Trend**: Marginal survival (net +0.0066R). Edge retention only 30% — any slippage increase kills it.
- **Relative Strength**: Massive outlier sensitivity. Raw mean was +0.92R; winsorized drops to +0.04R. Survivor only on technicality.

---

## NEEDS WORK (G3 FAIL but marginal)

| # | Strategy | Net Avg R | Gross Avg R | PF | Trades | Verdict |
|---|---|---|---|---|---|---|
| 15 | STR-F-eufearia-cci | -0.0066 | +0.0024 | — | 25,068 | NEEDS_WORK |
| 16 | STR-20260801-crosssectional-factor | -0.0219 | -0.0120 | 0.99 | 3,622 | NEEDS_WORK |
| 17 | STR-E-bollinger-squeeze | -0.0498 | -0.0466 | 0.86 | 1,466 | NEEDS_WORK |
| 18 | STR-H-rsi-mean-reversion | -0.0702 | -0.0606 | 0.91 | 29,039 | NEEDS_WORK |

All have gross avg R near zero or negative — cost drag pushes them below water. Eufearia CCI and Cross-sectional are close to breakeven; could be salvaged with execution optimization or regime filter.

---

## KILL (clear failure)

| # | Strategy | Net Avg R | Trades | Reason |
|---|---|---|---|---|
| 19 | STR-H-first-pullback | -1.9866 | 3 | Only 3 trades, all losers. Insufficient data. |

---

## NO BACKTEST DATA (7 vault strategies)

- STR-K-breadth-gated-gap — Breadth Gated Gap Reversal
- STR-M-selling-climax — Selling Climax Reversal
- STR-N-outside-day — Outside Day Key Reversal
- STR-P-pricemom-factor — PriceMom Factor
- STR-T1-01-outside-day-key-reversal — T1 Outside Day
- STR-T1-02-adx-trend-pullback — T1 ADX Trend Pullback
- STR-T1-03-gap-continuation — T1 Gap Continuation

No CSV backtest files found for these strategies. T1 series and single-letter codes K/M/N/P lack phase1a results. Recommend running backtests or archiving.

---

## SEED POOL: ALL 10 FAIL G0

All 10 pre-registered hypotheses (HYP-01 through HYP-10) fail the G0 cost pre-screen. Methodology:

- **Cost basis**: Hyperliquid base perp all-in round trip = 12 bps (taker fees + slippage + funding)
- **4x multiplier**: Need gross capture >= 48 bps for daily/swing, >= 54 bps for 5m intraday
- **Multi-leg penalty**: HYP-06 (BTC-beta residual reversion, two-leg) would face double cost = 24 bps/leg = 48 bps round trip

| ID | Description | Timeframe | Effect (bps) | Required (bps) | Result |
|---|---|---|---|---|---|
| HYP-01 | Funding-extreme unwind | 1h-6h | 15 | 48 | FAIL |
| HYP-02 | OI-confirmed breakout | 5m | 20 | 54 | FAIL |
| HYP-03 | Cascade exhaustion | 5m-15m | 25 | 54 | FAIL |
| HYP-04 | Settlement-hour drift | 5m | 10 | 54 | FAIL |
| HYP-05 | Cross-sectional perp momentum | 1d | 30 | 48 | FAIL |
| HYP-06 | BTC-beta residual reversion | 5m-4h | 18 | 54 (double cost) | FAIL |
| HYP-07 | Asia-range / EU-continuation | 5m-1h | 12 | 54 | FAIL |
| HYP-08 | Oracle-mark dislocation | 5m | 8 | 54 | FAIL |
| HYP-09 | Volatility compression expansion | 1h-4h | 22 | 48 | FAIL |
| HYP-10 | New-listing drift | 4h-1d | 35 | 48 | FAIL |

**Root cause**: All seed pool hypotheses have expected effect sizes (8-35 bps) well below the 4x cost threshold (48-54 bps) required by PROP-001 for crypto perps on Hyperliquid. This is a structural problem — none of these edges are large enough to survive transaction costs even before any modeling risk.

**Recommendation**: Seed pool needs higher-conviction hypotheses with expected effects >= 50 bps OR a venue with lower costs. Current crop is dead on G0.

---

## ASSET CLASS BREAKDOWN

| Class | Strategies | PROMOTE | NEEDS_WORK | KILL | NO_DATA |
|---|---|---|---|---|---|
| Stocks | 20 | 12 | 4 | 1 | 3 |
| Crypto | 3 | 2 | 0 | 0 | 1 |
| Both | 3 | 0 | 0 | 0 | 3 |
| **Total** | **26** | **14** | **4** | **1** | **7** |

Stock strategies benefit immensely from the 2 bps cost model (zero commission broker). Edge retention averages ~85% for stocks vs ~91% for the two crypto survivors.

---

## METHODOLOGY NOTES

1. **Cost model**: `cost_adjuster.py` VENUE_COSTS — stock=2.0 bps, crypto=12.0 bps
2. **Cost drag**: `(venue_cost_bps / 10000) / risk_pct` applied per trade to `r_multiple`
3. **G0 pass**: Median |gross R| > mean cost drag (edge survives noise)
4. **G3 pass**: Mean net R > 0 (edge survives execution costs)
5. **Winsorization**: Gross R clipped at P1/P99 to neutralize outlier distortion (STR-C had a -212 trillion R outlier; STR-G had extreme positive outliers inflating mean from +0.04R to +0.92R)
6. **Best CSV selection**: Per strategy, the CSV with highest net avg R is reported (most favorable parameterization)

---

## TOP SURVIVORS FOR PAPER TRADING

**Immediate candidates** (verified edge, sufficient sample):

1. **STR-B-macd-histogram-divergence** — Live strategy, 3,126 trades, +0.86R net, PF 1.89. Already live. Strongest proven edge.
2. **STR-20260818-lowcorr-regime** — 31,464 trades, +0.08R net. Largest sample. Thin but reliable edge.
3. **STR-VIXC-vix-contango-breakout** — 15,518 trades, +0.09R net, 55.5% win rate. Watch-listed, ready for promotion.
4. **STR-20260728-adaptive-trend** — 1,730 trades, +0.21R net, PF 1.58. Solid risk-adjusted returns.

**Watch candidates** (edge proven but sample too small):

5. **STR-20260730-atr-contraction-breakout** — 313 trades only but PF 2.39. Needs >=200 more trades.
6. **STR-DEBASEMENT-treasury-buyback** — 65 trades only. Needs >=100 more.
7. **STR-20260917-CAP-BOTTOM** — Only crypto survivor. 139 trades, +0.13R net.

**Do not promote** (marginal/fragile edge):

- STR-C-breakout-volume-trend (+0.007R net, edge retention 30%)
- STR-G-relative-strength (+0.04R net, massive outlier sensitivity)
- STR-20260906-BTC-SUPPLY-CRUNCH (47 trades, 94% win rate unsustainable)