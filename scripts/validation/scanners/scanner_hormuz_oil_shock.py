#!/usr/bin/env python3
"""
scanner_hormuz_oil_shock.py — STR-OIL-SHOCK: Hormuz Oil Shock Sector Rotation

Edge candidate: CAND-20260901-hormuz-oil-shock
Source hypothesis: Geopolitical oil supply shocks through the Strait of Hormuz
create a predictable cross-asset pattern: Energy stocks (XLE, XOM, CVX) benefit
from the risk premium expansion, while consumer discretionary (XLY) suffers from
higher gasoline prices → lower disposable income. The effect is amplified when
rising bond yields (CAND-20260901-global-bond-yield-surge) create a stagflationary
backdrop.

Signal Rules:
  Regime trigger (daily, from CL crude oil futures in data dict):
    1. CL price spikes >= SPIKE_PCT over SPIKE_LOOKBACK days (default: 5% in 2 days)
    2. Optional: XLE volume > 1.5x 20d average (institutional rotation into energy)
    3. Optional: VIX rising (fear entering market — confirms shock is being taken seriously)

  When regime active → Sector Rotation:
    LONG: XLE (energy sector), XOM, CVX (major integrated producers)
      - Entry at close on trigger bar
      - ATR-based stop below entry
      - Target: MIN_RR * risk
      - Max hold: MAX_BARS_HELD (default 20 trading days ~ 1 month)

    SHORT: XLY (consumer discretionary)
      - Airlines, restaurants, retailers suffer from higher gas prices
      - Same entry/stop/target logic (inverted for short)

Dependencies: pandas, numpy. CL and sector ETFs from main data dict.
"""

import numpy as np
import pandas as pd
from pathlib import Path

STRATEGY_ID = "STR-OIL-SHOCK"

# ── Parameters (module-level, monkey-patchable for walk-forward) ──────────────
SPIKE_LOOKBACK = 2            # Days over which to measure oil spike
SPIKE_PCT = 5.0              # CL must rise >= this % over lookback (e.g., 5% in 2 days)
VOLUME_MULT = 1.5            # XLE volume must be > this x 20d average (confirmation)
VIX_RISE_PCT = 3.0           # VIX must rise >= this % over lookback (fear confirmation)
ATR_PERIOD = 14
ATR_STOP_MULT = 2.0
MIN_RR = 1.5
MAX_BARS_HELD = 20           # ~1 month
REENTRY_COOLDOWN = 5          # Min bars between signals

# Targets
LONG_TICKERS = ["XLE", "XOM", "CVX"]   # Energy sector + major producers
SHORT_TICKERS = ["XLY"]                  # Consumer discretionary

# Cache for macro data
_CACHE_DIR = Path.home() / ".hermes" / "market_data"

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


def _load_series(ticker: str, col: str = "close") -> pd.Series:
    """Load a cached parquet and return the specified column as a Series."""
    p = _CACHE_DIR / f"{ticker}.parquet"
    if not p.exists():
        return pd.Series(dtype=float)
    df = pd.read_parquet(p)
    df.columns = [c.lower() for c in df.columns]
    df = df.sort_index()
    return df[col] if col in df.columns else df.iloc[:, 0]


def _load_regime(data: dict) -> pd.Series:
    """
    Build a date-indexed boolean Series: oil_shock_regime_active.

    Conditions:
      1. CL crude has risen >= SPIKE_PCT % over SPIKE_LOOKBACK days
      2. (Optional) XLE volume > VOLUME_MULT * 20d average
      3. (Optional) VIX rising >= VIX_RISE_PCT % over lookback
    """
    global _REGIME_SERIES, _REGIME_KEY
    key = (SPIKE_LOOKBACK, SPIKE_PCT, VOLUME_MULT, VIX_RISE_PCT)
    if _REGIME_SERIES is not None and _REGIME_KEY == key:
        return _REGIME_SERIES

    # CL from data dict or cache
    cl = None
    if "CL" in data:
        df = data["CL"].copy()
        df.columns = [c.lower() for c in df.columns]
        df.sort_index(inplace=True)
        cl = df["close"]
    else:
        cl = _load_series("CL")

    if cl is None or cl.empty or len(cl) < 100:
        _REGIME_SERIES = pd.Series(False, index=pd.DatetimeIndex([]))
        _REGIME_KEY = key
        return _REGIME_SERIES

    # VIX for fear confirmation
    vix = _load_series("VIXINDEX")

    # XLE volume for institutional rotation confirmation
    xle_vol = _load_series("XLE", col="volume") if "XLE" not in data else \
        data["XLE"]["volume"] if "volume" in data["XLE"].columns else pd.Series(dtype=float)

    # Align to CL index
    common_idx = cl.index
    if not vix.empty:
        common_idx = common_idx.intersection(vix.index)
    if xle_vol is not None and isinstance(xle_vol, pd.Series) and not xle_vol.empty:
        common_idx = common_idx.intersection(xle_vol.index)

    cl = cl.reindex(common_idx).ffill()
    if not vix.empty:
        vix = vix.reindex(common_idx).ffill()
    else:
        vix = pd.Series(index=common_idx, dtype=float)
    if xle_vol is not None and isinstance(xle_vol, pd.Series) and not xle_vol.empty:
        xle_vol = xle_vol.reindex(common_idx).ffill()
    else:
        xle_vol = pd.Series(index=common_idx, dtype=float)

    # Condition 1: CL spike
    cl_change = cl.pct_change(periods=SPIKE_LOOKBACK) * 100
    cond_cl_spike = cl_change >= SPIKE_PCT

    # Condition 2: VIX fear confirmation
    cond_vix = pd.Series(True, index=common_idx)
    if not vix.empty and vix.notna().sum() > SPIKE_LOOKBACK + 5:
        vix_change = vix.pct_change(periods=SPIKE_LOOKBACK) * 100
        cond_vix = vix_change >= VIX_RISE_PCT

    # Condition 3: XLE volume confirmation
    cond_volume = pd.Series(True, index=common_idx)
    if not xle_vol.empty and xle_vol.notna().sum() > 25:
        vol_ma20 = xle_vol.rolling(20, min_periods=20).mean()
        cond_volume = (xle_vol > vol_ma20 * VOLUME_MULT) & vol_ma20.notna()

    # All conditions
    regime = cond_cl_spike & cond_vix & cond_volume
    regime = regime.fillna(False)

    _REGIME_SERIES = regime
    _REGIME_KEY = key
    return _REGIME_SERIES


def _simulate_exit(closes, entry_idx, entry_price, stop_price, target_price, direction="long", max_bars=MAX_BARS_HELD):
    """Simulate forward exit: stop, target, or time."""
    n = len(closes)
    for offset in range(1, max_bars + 1):
        idx = entry_idx + offset
        if idx >= n:
            last = min(entry_idx + offset - 1, n - 1)
            return closes[last], "time", offset
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
    exit_idx = min(entry_idx + max_bars, n - 1)
    return closes[exit_idx], "time", max_bars


def scan(data: dict) -> list:
    """
    Batch scanner. Takes the full stock data dict.

    When oil-shock regime is active (CL spikes on geopolitical catalyst):
      - LONG XLE, XOM, CVX (energy sector + major producers)
      - SHORT XLY (consumer discretionary)
    """
    regime = _load_regime(data)
    if regime.empty:
        return []

    # Get all unique dates from the data dict
    all_dates = set()
    for df in data.values():
        all_dates.update(df.index)
    all_dates = sorted(all_dates)

    signals = []
    last_signal_date = None

    # Pre-compute ATR for CL for logging context (not used in signals)
    # CL from data dict
    cl_data = data.get("CL")
    if cl_data is not None:
        cl_close = cl_data["close"]

    for date_idx, current_date in enumerate(all_dates):
        # Check regime alignment
        if current_date not in regime.index:
            prior = regime[regime.index <= current_date]
            if prior.empty:
                continue
            regime_active = bool(prior.iloc[-1])
        else:
            regime_active = bool(regime.loc[current_date])

        if not regime_active:
            continue

        # Cooldown
        if last_signal_date is not None:
            days_since = (pd.Timestamp(current_date) - pd.Timestamp(last_signal_date)).days
            if days_since < REENTRY_COOLDOWN:
                continue

        # --- LONG signals: Energy sector ---
        for ticker in LONG_TICKERS:
            df = data.get(ticker)
            if df is None or len(df) < ATR_PERIOD + 5:
                continue

            mask = df.index <= current_date
            if mask.sum() < ATR_PERIOD + 5:
                continue

            df_slice = df[mask]
            entry_idx = len(df_slice) - 1
            entry_price = float(df_slice["close"].iloc[-1])

            atr = _compute_atr(df_slice["high"], df_slice["low"], df_slice["close"])
            atr_val = float(atr.iloc[-1])
            if atr_val <= 0 or np.isnan(atr_val):
                continue

            # Long
            stop_price = entry_price - ATR_STOP_MULT * atr_val
            risk = entry_price - stop_price
            if risk <= 0 or risk / entry_price < 0.002:
                continue
            target_price = entry_price + MIN_RR * risk

            closes = df_slice["close"].values.astype(float)
            ep, er, bh = _simulate_exit(
                closes, entry_idx, entry_price, stop_price, target_price, "long"
            )
            r_mult = (ep - entry_price) / risk

            signals.append({
                "ticker": ticker,
                "date": current_date,
                "direction": "long",
                "entry_price": round(entry_price, 4),
                "stop_price": round(float(stop_price), 4),
                "target_price": round(float(target_price), 4),
                "exit_price": round(float(ep), 4),
                "exit_reason": er,
                "r_multiple": round(float(r_mult), 4),
                "bars_held": bh,
                "strategy_id": STRATEGY_ID,
                "subperiod": _subperiod(pd.Timestamp(current_date)),
                "regime": "oil_shock",
                "entry_type": "energy_long",
            })

        # --- SHORT signals: Consumer discretionary ---
        for ticker in SHORT_TICKERS:
            df = data.get(ticker)
            if df is None or len(df) < ATR_PERIOD + 5:
                continue

            mask = df.index <= current_date
            if mask.sum() < ATR_PERIOD + 5:
                continue

            df_slice = df[mask]
            entry_idx = len(df_slice) - 1
            entry_price = float(df_slice["close"].iloc[-1])

            atr = _compute_atr(df_slice["high"], df_slice["low"], df_slice["close"])
            atr_val = float(atr.iloc[-1])
            if atr_val <= 0 or np.isnan(atr_val):
                continue

            # Short
            stop_price = entry_price + ATR_STOP_MULT * atr_val
            risk = stop_price - entry_price
            if risk <= 0 or risk / entry_price < 0.002:
                continue
            target_price = entry_price - MIN_RR * risk

            closes = df_slice["close"].values.astype(float)
            ep, er, bh = _simulate_exit(
                closes, entry_idx, entry_price, stop_price, target_price, "short"
            )
            r_mult = (entry_price - ep) / risk

            signals.append({
                "ticker": ticker,
                "date": current_date,
                "direction": "short",
                "entry_price": round(entry_price, 4),
                "stop_price": round(float(stop_price), 4),
                "target_price": round(float(target_price), 4),
                "exit_price": round(float(ep), 4),
                "exit_reason": er,
                "r_multiple": round(float(r_mult), 4),
                "bars_held": bh,
                "strategy_id": STRATEGY_ID,
                "subperiod": _subperiod(pd.Timestamp(current_date)),
                "regime": "oil_shock",
                "entry_type": "discretionary_short",
            })

        if signals:
            last_signal_date = current_date

    return signals


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from fetch_data import load_all

    print("Loading stock data...")
    stocks = load_all()
    print(f"  {len(stocks)} tickers loaded")

    print("\nRunning STR-OIL-SHOCK Hormuz oil shock scanner...")
    signals = scan(stocks)

    if not signals:
        print("No signals generated (regime may not have triggered historically).")
        sys.exit(0)

    r_values = [s["r_multiple"] for s in signals]
    short_sigs = [s for s in signals if s["direction"] == "short"]
    long_sigs = [s for s in signals if s["direction"] == "long"]
    wins = [s for s in signals if s["r_multiple"] > 0]

    avg_r = np.mean(r_values)
    win_rate = len(wins) / len(signals) if signals else 0

    print(f"\nSTR-OIL-SHOCK Phase 1A Results:")
    print(f"  Signals: {len(signals)} ({len(long_sigs)} long, {len(short_sigs)} short)")
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