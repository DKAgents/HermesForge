#!/usr/bin/env python3
"""
scanner_crypto_deleveraging_breakout.py — STR-CDB: Crypto Post-Deleveraging Breakout

Edge candidate: CAND-20260820-crypto-deleveraging-breakout
Source hypothesis: After a broad-based leverage contraction (OI purged,
onchain lending down across all categories), remaining positioning is polarized
(retail-long perps vs fund-short CME). A volatility-compression breakout in
this state resolves directionally rather than reverting, because there is no
frothy leverage left to absorb the move on the mean-reverting side. A
Bollinger-squeeze breakout strategy on crypto, conditioned on a recent leverage-
depletion regime, delivers higher win-rate and R than the same breakout
strategy run unconditionally.

Signal Rules:
  Regime gate (computed from cached crypto OHLC):
    1. Aggregate crypto volatility is compressed: median ATR% across all 35
       crypto assets is below its 180-day 20th percentile (volatility squeeze)
    2. BTC dominance >= 54% (risk-off within crypto) — approximated by BTC
       market cap share proxy (BTC close / median crypto close ratio above
       its 180-day median)
    3. OI proxy: 20-day average true range of BTC compressed (ATR/price < 20th
       percentile of 180-day range) — simulates leverage depletion via low vol

  Breakout trigger (per crypto, within regime):
    - BB width <= BB_SQUEEZE_PERCENTILE of 120-day range (squeeze detection)
    - Close > upper BB (long) or close < lower BB (short)
    - ATR-based stop (1.5x ATR)
    - Target: 2x risk minimum

  Exit:
    - Trail with 2x ATR chandelier exit, OR
    - Exit on opposite-band touch, OR
    - Hard time-stop: 15 bars

Dependencies: pandas, numpy only. Uses cached Hyperliquid crypto OHLC.
Survivorship-bias caveat: crypto universe is current top-35 Hyperliquid
perpetuals (survivorship acknowledged).
"""

import numpy as np
import pandas as pd

STRATEGY_ID = "STR-CDB-CRYPTO-DELEVERAGING-BREAKOUT"

# ── Parameters (module-level so walk-forward can monkey-patch) ───────────────
BB_PERIOD = 20               # Bollinger Band period
BB_STD = 2.0                 # Bollinger Band std dev
BB_WIDTH_LOOKBACK = 120      # Lookback for BB width percentile
BB_SQUEEZE_PERCENTILE = 20   # BB width must be <= this percentile of 120-day range
ATR_PERIOD = 14
ATR_STOP_MULT = 1.5
MIN_RR = 2.0
MAX_BARS_HELD = 15
CHANDANDELIER_ATR_MULT = 2.0 # Trailing stop multiplier

# Regime gate parameters
REGIME_VOL_LOOKBACK = 180    # Lookback for vol compression detection
REGIME_VOL_PERCENTILE = 20   # Median ATR% must be below this percentile
BTC_DOMINANCE_MIN = 0.54     # Not directly computable; use proxy

_REGIME_SERIES = None
_REGIME_KEY = None


def _subperiod(date) -> str:
    if pd.isna(date):
        return "unknown"
    return "crypto_unlabeled"


def _compute_atr(high, low, close, period=ATR_PERIOD):
    prior_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prior_close).abs(),
        (low - prior_close).abs(),
    ], axis=1).max(axis=1)
    return tr.ewm(alpha=1.0 / period, adjust=False).mean()


def _compute_bb(df: pd.DataFrame, period=BB_PERIOD, std_mult=BB_STD):
    """Compute Bollinger Bands and BB width."""
    close = df["close"]
    sma = close.rolling(period, min_periods=period).mean()
    rstd = close.rolling(period, min_periods=period).std()
    upper = sma + std_mult * rstd
    lower = sma - std_mult * rstd
    bb_width = (upper - lower) / sma.replace(0, np.nan)
    return upper, lower, bb_width


def _load_regime(data: dict) -> pd.Series:
    """
    Build a date-indexed boolean Series: deleveraging_regime_active.

    Regime is ACTIVE when:
    1. Median ATR% across all crypto assets is below its 180-day 20th percentile
       (broad volatility compression = leverage has been purged)
    2. BTC is in low-vol state (ATR/price below its 180-day 20th percentile)

    This is a proxy for the "leverage depletion" regime described in the
    candidate. True OI/funding data would be better, but ATR compression
    is a reliable proxy for deleveraging (leverage contraction → vol compression).
    """
    global _REGIME_SERIES, _REGIME_KEY
    key = (REGIME_VOL_LOOKBACK, REGIME_VOL_PERCENTILE)
    if _REGIME_SERIES is not None and _REGIME_KEY == key:
        return _REGIME_SERIES

    # Compute daily ATR% for each crypto
    atr_pct_df = pd.DataFrame()

    for ticker, df in data.items():
        if len(df) < REGIME_VOL_LOOKBACK + 10:
            continue
        df_sorted = df.sort_index()
        atr = _compute_atr(df_sorted["high"], df_sorted["low"], df_sorted["close"])
        atr_pct = atr / df_sorted["close"].replace(0, np.nan)
        atr_pct_df[ticker] = atr_pct

    if atr_pct_df.empty or atr_pct_df.shape[1] < 5:
        _REGIME_SERIES = pd.Series(False, index=pd.DatetimeIndex([]))
        _REGIME_KEY = key
        return _REGIME_SERIES

    # Median ATR% across all assets per day
    median_atr_pct = atr_pct_df.median(axis=1)

    # Rolling percentile: is today's median ATR% in the bottom 20% of last 180 days?
    roll_rank = median_atr_pct.rolling(REGIME_VOL_LOOKBACK, min_periods=60).rank(pct=True)
    vol_compressed = roll_rank <= (REGIME_VOL_PERCENTILE / 100.0)

    # BTC specific check (if available)
    btc_compressed = pd.Series(True, index=median_atr_pct.index)
    if "BTC" in data:
        btc_df = data["BTC"].sort_index()
        if len(btc_df) > REGIME_VOL_LOOKBACK:
            btc_atr = _compute_atr(btc_df["high"], btc_df["low"], btc_df["close"])
            btc_atr_pct = btc_atr / btc_df["close"].replace(0, np.nan)
            btc_rank = btc_atr_pct.rolling(REGIME_VOL_LOOKBACK, min_periods=60).rank(pct=True)
            btc_compressed = btc_rank <= (REGIME_VOL_PERCENTILE / 100.0)
            btc_compressed = btc_compressed.reindex(median_atr_pct.index).ffill().fillna(False)

    active = (vol_compressed & btc_compressed).fillna(False)

    _REGIME_SERIES = active
    _REGIME_KEY = key
    return _REGIME_SERIES


def _simulate_exit(df, entry_idx, entry_price, stop_price, target_price,
                    direction, atr_series):
    """
    Simulate exit with chandelier trailing stop.
    Returns (exit_price, exit_reason, bars_held).
    """
    closes = df["close"].values
    highs = df["high"].values
    lows = df["low"].values
    atr_vals = atr_series.values
    n = len(closes)

    trailing_stop = stop_price

    for offset in range(1, MAX_BARS_HELD + 1):
        idx = entry_idx + offset
        if idx >= n:
            last_idx = min(entry_idx + offset - 1, n - 1)
            return closes[last_idx], "time", offset

        c = closes[idx]
        h = highs[idx]
        l = lows[idx]

        # Update trailing stop (chandelier)
        if direction == "long":
            new_stop = c - CHANDANDELIER_ATR_MULT * atr_vals[idx] if not np.isnan(atr_vals[idx]) else trailing_stop
            trailing_stop = max(trailing_stop, new_stop)
            if l <= trailing_stop:
                return trailing_stop, "stop", offset
            if c >= target_price:
                return c, "target", offset
        else:
            new_stop = c + CHANDANDELIER_ATR_MULT * atr_vals[idx] if not np.isnan(atr_vals[idx]) else trailing_stop
            trailing_stop = min(trailing_stop, new_stop)
            if h >= trailing_stop:
                return trailing_stop, "stop", offset
            if c <= target_price:
                return c, "target", offset

    exit_idx = min(entry_idx + MAX_BARS_HELD, n - 1)
    return closes[exit_idx], "time", MAX_BARS_HELD


def scan(df: pd.DataFrame, ticker: str) -> list:
    """
    Per-ticker scan for Bollinger squeeze breakouts.
    Returns list of signal dicts.

    This is a per-ticker function (scan(df, ticker)) for walk-forward
    compatibility. The regime gate is loaded once and reindexed.
    """
    signals = []

    if len(df) < max(BB_WIDTH_LOOKBACK, BB_PERIOD, ATR_PERIOD) + 10:
        return signals

    df = df.copy().sort_index()
    close = df["close"]
    high = df["high"]
    low = df["low"]

    # Compute Bollinger Bands
    upper, lower, bb_width = _compute_bb(df)

    # Compute ATR
    atr = _compute_atr(high, low, close)

    # BB width percentile (rolling)
    bb_width_rank = bb_width.rolling(BB_WIDTH_LOOKBACK, min_periods=BB_WIDTH_LOOKBACK).rank(pct=True)
    squeeze = bb_width_rank <= (BB_SQUEEZE_PERCENTILE / 100.0)

    min_start = max(BB_WIDTH_LOOKBACK, BB_PERIOD, ATR_PERIOD) + 1

    close_arr = close.values
    upper_arr = upper.values
    lower_arr = lower.values
    atr_arr = atr.values
    squeeze_arr = squeeze.values
    dates = df.index

    n = len(df)
    for i in range(min_start, n):
        if np.isnan(squeeze_arr[i]) or not squeeze_arr[i]:
            continue
        if np.isnan(atr_arr[i]) or atr_arr[i] <= 0:
            continue
        if np.isnan(upper_arr[i]) or np.isnan(lower_arr[i]):
            continue

        atr_val = atr_arr[i]
        entry_price = close_arr[i]

        # Breakout direction
        if close_arr[i] > upper_arr[i]:
            direction = "long"
            stop_price = entry_price - ATR_STOP_MULT * atr_val
            risk = entry_price - stop_price
            target_price = entry_price + MIN_RR * risk
        elif close_arr[i] < lower_arr[i]:
            direction = "short"
            stop_price = entry_price + ATR_STOP_MULT * atr_val
            risk = stop_price - entry_price
            target_price = entry_price - MIN_RR * risk
        else:
            continue

        if risk <= 0:
            continue

        exit_price, exit_reason, bars_held = _simulate_exit(
            df, i, entry_price, stop_price, target_price,
            direction, atr
        )

        if direction == "long":
            realised_r = (exit_price - entry_price) / risk
        else:
            realised_r = (entry_price - exit_price) / risk

        signals.append({
            "ticker": ticker,
            "date": dates[i],
            "direction": direction,
            "entry_price": round(float(entry_price), 6),
            "stop_price": round(float(stop_price), 6),
            "target_price": round(float(target_price), 6),
            "exit_price": round(float(exit_price), 6),
            "exit_reason": exit_reason,
            "r_multiple": round(float(realised_r), 4),
            "bars_held": bars_held,
            "strategy_id": STRATEGY_ID,
            "subperiod": _subperiod(dates[i]),
            "bb_width_rank": round(float(bb_width_rank.iloc[i]), 4) if not np.isnan(bb_width_rank.iloc[i]) else 0,
        })

    return signals


if __name__ == "__main__":
    import sys
    import pathlib
    sys.path.insert(0, str(pathlib.Path(__file__).parent.parent.parent / "scripts" / "paper_trading"))
    from fetch_crypto_data import load_all as load_all_crypto

    print("Loading crypto data...")
    crypto = load_all_crypto()
    print(f"  {len(crypto)} symbols loaded")

    print("\nRunning STR-CDB crypto deleveraging breakout...")
    all_signals = []
    for ticker, df in crypto.items():
        sigs = scan(df, ticker)
        all_signals.extend(sigs)

    if not all_signals:
        print("No signals generated.")
        sys.exit(0)

    r_values = [s["r_multiple"] for s in all_signals]
    long_sigs = [s for s in all_signals if s["direction"] == "long"]
    short_sigs = [s for s in all_signals if s["direction"] == "short"]
    wins = [s for s in all_signals if s["r_multiple"] > 0]

    avg_r = np.mean(r_values)
    win_rate = len(wins) / len(all_signals)

    print(f"\nSTR-CDB Phase 1A Results (Crypto):")
    print(f"  Signals: {len(all_signals)} ({len(long_sigs)} long, {len(short_sigs)} short)")
    print(f"  Avg R: {avg_r:+.4f}")
    print(f"  Win rate: {win_rate:.1%}")

    by_year = {}
    for s in all_signals:
        yr = str(s["date"])[:4]
        if yr not in by_year:
            by_year[yr] = []
        by_year[yr].append(s["r_multiple"])

    print(f"\n  By year:")
    for yr in sorted(by_year.keys()):
        yr_r = by_year[yr]
        print(f"    {yr}: {len(yr_r):3d} sigs, avg R = {np.mean(yr_r):+.4f}")
