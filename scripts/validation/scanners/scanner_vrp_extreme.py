#!/usr/bin/env python3
"""
scanner_vrp_extreme.py — STR-20261001-VRP-EXTREME-BREAKOUT

Edge candidate: CAND-20261001-vrp-extreme
Source: Volatility risk premium extreme (+5.9%, VIX overestimating fear)

Hypothesis: Large positive VRP → market pricing in too much fear, likely to
resolve with VIX compression (bullish). Buy stocks breaking out (VIX should
compress) when VRP > VRP_ENTRY_THRESHOLD.

Signal Rules (batch mode, uses VIX + stock universe):
  1. Load VIX data, compute realized vol (20d SPY return std annualized)
  2. VRP = VIX_close - realized_vol
  3. VRP-active day: VRP > VRP_ENTRY_THRESHOLD AND VIX < VIX_CEILING
     (market is pricing in excess fear but VIX not at crisis level)
  4. Per-ticker entry (all required on signal day i):
     - close[i] > max(close[i-20:i])  20-day breakout
     - volume[i] > VOL_MULT * avg_vol(20d)  volume expansion
     - close[i] > MA50[i]  trend agreement
     - ATR% of price <= MAX_ATR_PCT  avoid extreme names
  5. Exit: stop below MA20 or entry-day low, target MIN_RR * risk
  6. Time stop at MAX_BARS_HELD

Dependencies: pandas, numpy. VIX/VIX3M loaded from local parquet cache.
Uses SPY for realized vol computation (fallback: SPY close series).
"""

import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime

STRATEGY_ID = "STR-20261001-VRP-EXTREME-BREAKOUT"

# ── Parameters (module-level; walk-forward monkey-patches these) ────────────
VRP_ENTRY_THRESHOLD = 3.0      # VRP > +3% = excess fear regime
VIX_CEILING = 25.0             # Don't trade when VIX above crisis level
REALIZED_VOL_LOOKBACK = 20     # Days for realized vol computation
BREAKOUT_LOOKBACK = 20
VOL_AVG_PERIOD = 20
VOL_MULT = 1.2                 # Volume must be > 1.2x average
MA_TREND = 50
MA_STOP = 20
MIN_RR = 2.0
STOP_BUFFER_ATR = 0.5
MAX_ATR_PCT = 0.08
ATR_PERIOD = 14
MAX_BARS_HELD = 12
REENTRY_COOLDOWN = 10
MIN_HISTORY = 60

_CACHE_DIR = Path.home() / ".hermes" / "market_data"
_VIX_CACHE = _CACHE_DIR / "VIXINDEX.parquet"
_SPY_CACHE = _CACHE_DIR / "SPY.parquet"
# Cached regime series
_REGIME_SERIES = None
_REGIME_KEY = None


def _subperiod(date) -> str:
    if pd.isna(date):
        return "unknown"
    d = date.date() if hasattr(date, "date") else date
    if d < pd.Timestamp("2019-04-01").date():
        return "pre_warmup"
    if d <= pd.Timestamp("2021-12-31").date():
        return "period1_bull"
    if d <= pd.Timestamp("2023-12-31").date():
        return "period2_bear"
    return "period3_current"


def _compute_atr(high, low, close, period=ATR_PERIOD):
    prior_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prior_close).abs(),
        (low - prior_close).abs(),
    ], axis=1).max(axis=1)
    return tr.ewm(alpha=1.0 / period, adjust=False).mean()


def _compute_vrp_regime() -> pd.Series:
    """Build a date-indexed boolean series: vrp_active.
    
    VRP = VIX_close - realized_vol(20d SPY returns, annualized %).
    Active when VRP > VRP_ENTRY_THRESHOLD and VIX < VIX_CEILING.
    """
    global _REGIME_SERIES, _REGIME_KEY
    key = (VRP_ENTRY_THRESHOLD, VIX_CEILING, REALIZED_VOL_LOOKBACK)
    if _REGIME_SERIES is not None and _REGIME_KEY == key:
        return _REGIME_SERIES

    if not _VIX_CACHE.exists():
        return pd.Series(dtype=bool)
    if not _SPY_CACHE.exists():
        return pd.Series(dtype=bool)

    vix = pd.read_parquet(_VIX_CACHE)
    vix.columns = [c.lower() for c in vix.columns]
    vix = vix.sort_index()
    vix_close = vix["close"]

    spy = pd.read_parquet(_SPY_CACHE)
    spy.columns = [c.lower() for c in spy.columns]
    spy = spy.sort_index()
    spy_close = spy["close"]

    # Realized vol: 20-day rolling std of SPY daily returns, annualized
    spy_ret = spy_close.pct_change().dropna()
    realized_vol = spy_ret.rolling(window=REALIZED_VOL_LOOKBACK, min_periods=5).std()
    realized_vol = realized_vol * np.sqrt(252) * 100  # Annualized to percent

    # Align VIX with realized vol dates
    common_idx = vix_close.index.intersection(realized_vol.index)
    vix_aligned = vix_close.reindex(common_idx)
    rv_aligned = realized_vol.reindex(common_idx)

    vrp = vix_aligned - rv_aligned
    vrp_active = (vrp > VRP_ENTRY_THRESHOLD) & (vix_aligned < VIX_CEILING)

    _REGIME_SERIES = vrp_active.astype(bool)
    _REGIME_KEY = key
    return _REGIME_SERIES


def scan(data_dict: dict) -> list:
    """Batch-mode scanner: market-wide VRP extreme → stock breakouts.

    Args:
        data_dict: {ticker: DataFrame} of stock OHLCV.

    Returns:
        list of signal dicts.
    """
    if not data_dict:
        return []

    vrp_active = _compute_vrp_regime()
    if len(vrp_active) < MIN_HISTORY:
        return []

    signals = []

    for ticker, df in data_dict.items():
        if len(df) < MIN_HISTORY:
            continue

        df = df.copy()
        df.columns = [c.lower() for c in df.columns]
        df.sort_index(inplace=True)

        close = df["close"] if "close" in df.columns else df.iloc[:, 3]
        high = df["high"] if "high" in df.columns else df.iloc[:, 1]
        low = df["low"] if "low" in df.columns else df.iloc[:, 2]
        volume = df["volume"] if "volume" in df.columns else (
            df["vol"] if "vol" in df.columns else pd.Series(1.0, index=df.index))
        dates = df.index

        # Align VRP regime to this ticker's dates
        ticker_vrp = vrp_active.reindex(dates).fillna(False).values

        # Compute rolling values
        atr_series = _compute_atr(high, low, close)
        ma50 = close.rolling(window=MA_TREND, min_periods=5).mean()
        ma20 = close.rolling(window=MA_STOP, min_periods=5).mean()
        vol_avg = volume.rolling(window=VOL_AVG_PERIOD, min_periods=5).mean()

        close_arr = close.values
        high_arr = high.values
        low_arr = low.values
        vol_arr = volume.values
        atr_arr = atr_series.values
        vol_avg_arr = vol_avg.values
        ma50_arr = ma50.values
        ma20_arr = ma20.values

        last_signal_idx = -REENTRY_COOLDOWN

        for i in range(BREAKOUT_LOOKBACK, len(dates) - 1):
            # Check VRP regime gate
            if not ticker_vrp[i]:
                continue

            # Re-entry cooldown
            if i - last_signal_idx < 10:
                continue

            # 20-day breakout: close > max of prior 20 closes
            prior_window = close_arr[max(0, i - BREAKOUT_LOOKBACK):i]
            if len(prior_window) < 5:
                continue
            if close_arr[i] <= prior_window.max():
                continue

            # Volume expansion
            if vol_avg_arr[i] > 0 and vol_arr[i] < VOL_MULT * vol_avg_arr[i]:
                continue

            # Trend agreement
            if np.isnan(ma50_arr[i]) or close_arr[i] <= ma50_arr[i]:
                continue

            # ATR sanity check
            price = close_arr[i]
            if atr_arr[i] / price > MAX_ATR_PCT or np.isnan(atr_arr[i]):
                continue

            # Build stop and target
            stop_price = min(ma20_arr[i], low_arr[i]) - STOP_BUFFER_ATR * atr_arr[i]
            risk = price - stop_price
            if risk <= 0 or risk / price < 0.002:
                continue
            target_price = price + MIN_RR * risk

            # Simulate exit forward
            ep, er, bh = "stop", MAX_BARS_HELD, MAX_BARS_HELD
            for offset in range(1, MAX_BARS_HELD + 1):
                idx = i + offset
                if idx >= len(dates):
                    bh = offset - 1
                    ep = float(close_arr[-1])
                    er = "time"
                    break
                c = float(close_arr[idx])
                if c >= target_price:
                    ep = c
                    er = "target"
                    bh = offset
                    break
                if c <= stop_price:
                    ep = c
                    er = "stop"
                    bh = offset
                    break
            else:
                ep = float(close_arr[min(i + MAX_BARS_HELD, len(dates) - 1)])
                er = "time"

            r_mult = (ep - price) / risk

            ts = pd.Timestamp(dates[i])
            signals.append({
                "ticker": ticker,
                "date": ts.date(),
                "direction": "long",
                "entry_price": round(float(price), 4),
                "stop_price": round(float(stop_price), 4),
                "target_price": round(float(target_price), 4),
                "exit_price": round(float(ep), 4),
                "exit_reason": er,
                "r_multiple": round(float(r_mult), 4),
                "bars_held": int(bh),
                "subperiod": _subperiod(ts),
                "strategy_id": STRATEGY_ID,
            })
            last_signal_idx = i

    return signals


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from fetch_data import load_all
    data = load_all()
    sigs = scan(data)
    print(f"VRP Extreme scanner: {len(sigs)} signals")
    if sigs:
        r_vals = [s["r_multiple"] for s in sigs]
        wr = sum(1 for r in r_vals if r > 0) / len(r_vals)
        print(f"  Mean R: {np.mean(r_vals):.4f}, Win rate: {wr:.1%}")