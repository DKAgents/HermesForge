#!/usr/bin/env python3
"""
scanner_treasury_debasement.py — STR-DEBASEMENT: Treasury Buyback / Dollar Debasement Regime Trade

Edge candidate: CAND-20260825-treasury-buyback-debasement-regime
Source hypothesis: US Treasury doubling bond buybacks (Aug 19, 2026) has activated
a structural dollar debasement regime. When DXY is weakening, gold is rallying,
and BTC is in an uptrend, long BTC on pullbacks to moving averages. The regime
trade holds 4-8 weeks with clear catalyst-defined entry.

Signal Rules:
  Regime gate (computed from cached GLD/DXY/TNX data):
    1. DXY < 50-day SMA (dollar weakening)
    2. GLD > 20-day SMA (gold rallying - hard asset bid)
    3. BTC > 50-day SMA (structural bull trend)
    4. US10Y yield change declining (yield suppression → debasement)

  Entry trigger (per BTC bar within regime):
    1. Regime gate active (all 3 conditions met)
    2. BTC above 50-day SMA (structural bull regime)
    3. Entry on any bar when regime first becomes active after a period of inactivity
       or BTC has pulled back within 10% of 20MA
    4. ATR-based stop (1.5x ATR below entry)
    5. Target: 2x risk minimum

  Exit:
    - Stop loss (1.5x ATR)
    - Target (2x risk)
    - Max hold: 20 bars (~4 weeks, aligns with 4-8 week thesis)

Dependencies: pandas, numpy, pathlib. Loads BTC from crypto cache,
GLD/DXY/TNX from stock market_data cache.
"""

import numpy as np
import pandas as pd
from pathlib import Path

STRATEGY_ID = "STR-DEBASEMENT-TREASURY-BUYBACK"

# ── Parameters (module-level so walk-forward can monkey-patch) ────────────────
DXY_SMA_FAST = 20            # DXY short MA for trend detection
DXY_SMA_SLOW = 50            # DXY longer MA - must be below this for weakening
GLD_SMA = 20                 # Gold must be above this MA (uptrend)
BTC_MA_TREND = 50            # BTC must be above this for structural bull
BTC_MA_ENTRY = 20            # BTC pullback to this MA for entry
ATR_PERIOD = 14
ATR_STOP_MULT = 1.5
MIN_RR = 2.0
MAX_BARS_HELD = 20           # 4 weeks (20 trading days)
REENTRY_COOLDOWN = 10        # Min bars between signals on same ticker
YIELD_DECLINE_LOOKBACK = 10  # TNX change over this many days
PULLBACK_PCT = 0.10         # Max deviation from 20MA for pullback entry (10%)

# Cache paths for macro data
_DXY_CACHE = Path.home() / ".hermes" / "market_data" / "DXY.parquet"
_GLD_CACHE = Path.home() / ".hermes" / "market_data" / "GLD.parquet"

# Cached regime series (built once per parameter set, reused across tickers)
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


def _load_macro_regime() -> pd.Series:
    """Build a date-indexed boolean Series: debasement_regime_active.

    Simplified regime (drops TNX condition for more frequent signals):
    1. DXY < 50-day SMA (dollar weakening trend)
    2. GLD > 20-day SMA (gold in uptrend — hard asset bid)
    """
    global _REGIME_SERIES, _REGIME_KEY
    key = (DXY_SMA_FAST, DXY_SMA_SLOW, GLD_SMA)
    if _REGIME_SERIES is not None and _REGIME_KEY == key:
        return _REGIME_SERIES

    def _load_single(path, ticker_label) -> pd.Series:
        df = pd.read_parquet(path)
        df.columns = [c.lower() for c in df.columns]
        df = df.sort_index()
        return df["close"]

    try:
        dxy_close = _load_single(_DXY_CACHE, "DXY")
        gld_close = _load_single(_GLD_CACHE, "GLD")
    except Exception as e:
        print(f"  [TREASURY-DEBASEMENT] WARN: Could not load macro data: {e}")
        _REGIME_SERIES = pd.Series(False, index=pd.DatetimeIndex([]))
        _REGIME_KEY = key
        return _REGIME_SERIES

    # Common date index
    common_index = dxy_close.index.intersection(gld_close.index)
    if len(common_index) < 100:
        _REGIME_SERIES = pd.Series(False, index=pd.DatetimeIndex([]))
        _REGIME_KEY = key
        return _REGIME_SERIES

    dxy = dxy_close.reindex(common_index).ffill()
    gld = gld_close.reindex(common_index).ffill()

    # Compute MAs
    dxy_sma50 = dxy.rolling(DXY_SMA_SLOW, min_periods=DXY_SMA_SLOW).mean()
    gld_sma20 = gld.rolling(GLD_SMA, min_periods=GLD_SMA).mean()

    # Regime conditions
    dxy_weakening = dxy < dxy_sma50
    gold_uptrend = gld > gld_sma20

    regime = dxy_weakening & gold_uptrend

    _REGIME_SERIES = regime.fillna(False)
    _REGIME_KEY = key
    return _REGIME_SERIES


def _simulate_exit(df, entry_idx, entry_price, stop_price, target_price, direction="long"):
    closes = df["close"].values
    n = len(closes)
    for offset in range(1, MAX_BARS_HELD + 1):
        idx = entry_idx + offset
        if idx >= n:
            last_idx = min(entry_idx + offset - 1, n - 1)
            return closes[last_idx], "time", offset
        c = closes[idx]
        if direction == "long":
            if c >= target_price:
                return c, "target", offset
            if c <= stop_price:
                return c, "stop", offset
        else:
            if c <= target_price:
                return c, "target", offset
            if c >= stop_price:
                return c, "stop", offset
    exit_idx = min(entry_idx + MAX_BARS_HELD, n - 1)
    return closes[exit_idx], "time", MAX_BARS_HELD


def scan(data: dict, latest_only: bool = False) -> list:
    """
    Batch scanner: takes crypto data dict, uses BTC for signal generation
    and macro data (GLD, DXY, TNX) for regime detection.

    Entry logic:
    1. Macro regime must be active (DXY weakening + Gold uptrend)
    2. BTC must be in structural uptrend (> 50 SMA)
    3. Two entry types:
       a) REGIME ENTRY: First bar where regime becomes active after being inactive
       b) PULLBACK ENTRY: BTC price near 20MA (within PULLBACK_PCT) during active regime
    4. ATR-based stop, target at MIN_RR

    Parameters
    ----------
    data : dict
        {ticker: DataFrame} mapping for crypto symbols (must include BTC)
    latest_only : bool
        If True, only return signals from the most recent bar date
        (for paper trading daily capture)

    Returns
    -------
    list of signal dicts
    """
    if "BTC" not in data:
        return []

    btc_df = data["BTC"].copy().sort_index()
    if len(btc_df) < max(ATR_PERIOD, BTC_MA_TREND, BTC_MA_ENTRY) + 20:
        return []

    # Load macro regime
    macro_regime = _load_macro_regime()
    if macro_regime.empty:
        return []

    # Align regime to BTC dates
    regime_aligned = macro_regime.reindex(btc_df.index, method="ffill").fillna(False)

    close = btc_df["close"]
    high = btc_df["high"]
    low = btc_df["low"]

    # Compute indicators
    atr = _compute_atr(high, low, close)
    btc_sma50 = close.rolling(BTC_MA_TREND, min_periods=BTC_MA_TREND).mean()
    btc_sma20 = close.rolling(BTC_MA_ENTRY, min_periods=BTC_MA_ENTRY).mean()

    # Detect regime activation (first bar where regime turns on after being off)
    regime_prev = regime_aligned.shift(1).fillna(False)
    regime_activation = regime_aligned & ~regime_prev

    min_start = max(ATR_PERIOD, BTC_MA_TREND, BTC_MA_ENTRY) + 1
    close_arr = close.values
    atr_arr = atr.values
    sma50_arr = btc_sma50.values
    sma20_arr = btc_sma20.values
    reg_arr = regime_aligned.values
    reg_act_arr = regime_activation.values
    dates = btc_df.index

    signals = []
    last_signal_bar = -999  # Cooldown tracking

    n = len(btc_df)
    for i in range(min_start, n):
        # Check cooldown
        if i - last_signal_bar < REENTRY_COOLDOWN:
            continue

        # Regime check: macro conditions must be favorable
        if not bool(reg_arr[i]):
            continue

        # BTC structural trend check: must be above 50 SMA (bull regime)
        if np.isnan(sma50_arr[i]) or close_arr[i] <= sma50_arr[i]:
            continue

        if np.isnan(atr_arr[i]) or atr_arr[i] <= 0:
            continue

        # Entry Type A: Regime activation (first bar of new regime)
        regime_entry = bool(reg_act_arr[i])

        # Entry Type B: Pullback to 20MA during active regime
        pullback_entry = False
        if not np.isnan(sma20_arr[i]):
            dist_to_ma = (close_arr[i] - sma20_arr[i]) / sma20_arr[i]
            # Price within PULLBACK_PCT of 20MA (above or below by <= PULLBACK_PCT)
            pullback_entry = abs(dist_to_ma) <= PULLBACK_PCT

        if not (regime_entry or pullback_entry):
            continue

        entry_price = close_arr[i]
        stop_price = entry_price - ATR_STOP_MULT * atr_arr[i]
        risk = entry_price - stop_price
        if risk <= 0 or risk / entry_price < 0.003:
            continue

        target_price = entry_price + MIN_RR * risk

        exit_price, exit_reason, bars_held = _simulate_exit(
            btc_df, i, entry_price, stop_price, target_price, "long"
        )
        realised_r = (exit_price - entry_price) / risk

        signals.append({
            "ticker": "BTC",
            "date": dates[i],
            "direction": "long",
            "entry_price": round(float(entry_price), 2),
            "stop_price": round(float(stop_price), 2),
            "target_price": round(float(target_price), 2),
            "exit_price": round(float(exit_price), 2),
            "exit_reason": exit_reason,
            "r_multiple": round(float(realised_r), 4),
            "bars_held": bars_held,
            "strategy_id": STRATEGY_ID,
            "subperiod": _subperiod(dates[i]),
            "entry_type": "regime" if regime_entry else "pullback",
            "regime_active": bool(reg_arr[i]),
        })
        last_signal_bar = i

    # Filter for latest_only mode (paper trading daily capture)
    if latest_only and signals:
        latest_date = max(s["date"] for s in signals)
        signals = [s for s in signals if s["date"] == latest_date]

    return signals


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent / "paper_trading"))
    from fetch_crypto_data import load_all as load_all_crypto

    print("Loading crypto data...")
    crypto = load_all_crypto()
    print(f"  {len(crypto)} symbols loaded")

    print("\nRunning STR-DEBASEMENT treasury buyback scanner...")
    signals = scan(crypto)

    if not signals:
        print("No signals generated.")
        sys.exit(0)

    r_values = [s["r_multiple"] for s in signals]
    wins = [s for s in signals if s["r_multiple"] > 0]

    avg_r = np.mean(r_values)
    win_rate = len(wins) / len(signals) if signals else 0

    print(f"\nSTR-DEBASEMENT Phase 1A Results (Crypto):")
    print(f"  Signals: {len(signals)} (all long)")
    print(f"  Avg R: {avg_r:+.4f}")
    print(f"  Win rate: {win_rate:.1%}")
    print(f"  Avg win: {np.mean([s['r_multiple'] for s in wins]):+.4f}" if wins else "")

    by_year = {}
    for s in signals:
        yr = str(s["date"])[:4]
        if yr not in by_year:
            by_year[yr] = []
        by_year[yr].append(s["r_multiple"])

    print(f"\n  By year:")
    for yr in sorted(by_year.keys()):
        yr_r = by_year[yr]
        print(f"    {yr}: {len(yr_r):3d} sigs, avg R = {np.mean(yr_r):+.4f}")