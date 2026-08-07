# STR-H - Hype / Momentum Ignition - Walk-Forward Validation

**Strategy ID:** `STR-H-HYPE-IGNITION`  
**Generated:** 2026-08-07T00:57:13.152583Z  
**Direction:** Long-only  
**Asset class:** Crypto only  
**Risk per trade:** 0.5% account  
**Timeframe:** Daily bars (see note below)

---

## 1. Thesis

Retail "hype" episodes (social-media-driven momentum) tend to 
leave a footprint in on-chart volume *before* the move is obvious. 
This strategy detects that footprint with a **volume acceleration** 
proxy and enters on the first pullback to the 8-EMA, trailing out 
behind the same EMA while a structural swing-low stop protects capital.

## 2. Honest Limitations

- **Social-volume proxy.** We have no social-media data (Twitter/X, 
  Reddit, LunarCrush) under the free-data constraint. The 3x 7-bar 
  volume spike is a structural proxy for attention-driven flow, but 
  it cannot distinguish organic hype from institutional rebalancing, 
  exchange listings, or news-driven volume. Treat results as 
  a *volume-momentum* strategy, not a confirmed social-sentiment strategy.
- **Timeframe deviation.** The spec calls for 4h crypto bars; the 
  project's cached free-data infrastructure (Hyperliquid fetcher + 
  parquet cache) uses daily bars. This run uses daily bars. 
  The strategy logic is timeframe-agnostic, so the daily results are a 
  lower-frequency (and more conservative) proxy for the 4h version.
- **Survivorship bias.** The crypto universe is the current set of 
  liquid Hyperliquid perpetual markets; previously delisted coins 
  (e.g. FTM, MATIC, RNDR, LUNA-class) were already excluded from the 
  cache. This is survivorship bias against failed projects, which is 
  *most acute for a hype strategy* since many hype-driven coins 
  subsequently went to zero.
- **Crypto volume quality.** ~42% of Hyperliquid daily bars report 
  zero volume. A baseline-health guard requires >=4 of the prior 7 bars 
  to have non-zero volume before a spike is counted, preventing false 
  spikes from degenerate zero-baselines.
- **Look-ahead-free.** All rolling means use `.shift(1)` so the 
  ignition bar never contaminates its own baseline. Entries/exits are 
  simulated on subsequent bars only.

## 3. Signal Rules

- **Volume spike:** `volume > 3.0x mean(prior 7 bars)`
- **Momentum ignition:** `(close-low)/(high-low) >= 0.75` (close in top 25% of range)
- **Volume expansion:** `volume >= 2.0x mean(prior 20 bars)`
- **Regime filter:** BTC > SMA(50)

## 4. Entry / Stop / Exit

- **Scale-in:** 50% at ignition close; 50% on first pullback to 8-EMA within 3 bars (fill at EMA), else market on bar 3.
- **Stop:** swing low of the 5 bars preceding the ignition candle (structural, long-side).
- **Trailing exit:** daily close < 8-EMA.
- **Hard exit:** daily close < 21-EMA.
- **Time stop:** 3 bars if the trade has not moved >= 2.0R in favor.
- **Max-hold cap:** 40 bars (backtest boundedness).
- **Costs:** crypto 5bp round-trip.

## 5. Walk-Forward Results

Split: train = first 70% of bars by date. test = last 30%.

### Performance Table

| Period | Trades | Win Rate | Mean R | Total R | Sharpe (per-trade) | Max DD (R) | Avg Hold (bars) |
|--------|--------|----------|--------|---------|--------------------|------------|-----------------|
| Crypto train | 93 | 58.1% | +0.115 | +10.67 | +0.17 | 4.05 | 3.0 |
| Crypto test | 122 | 32.8% | +0.142 | +17.27 | +0.05 | 10.88 | 2.6 |
| Crypto all | 215 | 43.7% | +0.130 | +27.95 | +0.06 | 11.51 | 2.7 |

### Exit-Reason Breakdown

**Crypto train** (93 trades):
  time_stop=53 . trail_ema8=23 . hard_ema21=10 . stop=5 . stop_pre_scalein=2

**Crypto test** (122 trades):
  time_stop=44 . trail_ema8=32 . hard_ema21=26 . stop_pre_scalein=16 . stop=4

**Crypto all** (215 trades):
  time_stop=97 . trail_ema8=55 . hard_ema21=36 . stop_pre_scalein=18 . stop=9

## 6. Verdict

- **Crypto:** MARGINAL OOS - test mean R positive but thin; monitor before allocating capital.

> Sharpe here is **per-trade, R-based** (mean R / std R), not the annualized portfolio Sharpe. For an episodic event strategy, per-trade Sharpe is the honest unit; annualization would require an assumption about trade frequency that the data do not support.

## 7. Survivorship & Data-Quality Notes (repeated for emphasis)

- Crypto universe: **35** Hyperliquid markets (survivorship-biased).
- Crypto train/test cutoff: `2024-10-21`
- Delisted coins during the backtest window are excluded -> forward-looking survivorship bias, *most acute for a hype strategy* because many hyped assets subsequently collapsed to zero.
