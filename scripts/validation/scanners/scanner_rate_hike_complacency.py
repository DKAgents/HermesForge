#!/usr/bin/env python3
"""
scanner_rate_hike_complacency.py — STR-RHC: Rate-Hike Complacency Divergence

Edge candidate: CAND-20260820-rate-hike-complacency-divergence
Source hypothesis: When rate-hike-implied path steepens (2yr Treasury yield
rising) while VIX is at multi-month lows and equities are near ATH, forward
1-3 month equity risk premium is negatively skewed. A defensive sector
rotation (long low-beta/defensive sectors, short high-beta/momentum) earns
positive expected return because the market has under-priced policy tightening.

Signal Rules:
  Regime trigger (daily, computed from cached ^VIX, ^IRX, ^TNX, SPY):
    1. VIX <= VIX_MAX (complacency floor, default 16)
    2. SPY within NEAR_ATH_PCT of its 60-day high (default 2%)
    3. 2yr yield (IRX proxy) has risen >= YIELD_RISE_BPS over prior 20 days
    4. 2s10s spread (TNX - IRX) has flattened/inverted further over same window
  When all 4 conditions hold → FIRE defensive rotation.

  Trade: Long XLP/XLV/XLU (defensive), Short XLK/XLY (cyclical)
    - Equal-dollar, beta-neutral adjusted
    - Weekly rebalance while trigger holds
    - Exit: stop at ATR_STOP_MULT × ATR from entry, or time stop at MAX_BARS_HELD

Dependencies: pandas, numpy. VIX/IRX/TNX/SPY/sector ETFs loaded from local
parquet cache (~/.hermes/market_data/).

Survivorship-bias caveat: universe is current S&P constituents (ADR-004).
Transaction costs NOT modeled here — Phase 1A is frictionless; walk-forward
applies spread+commission+gap costs.
"""

import numpy as np
import pandas as pd
from pathlib import Path

STRATEGY_ID = "STR-RHC-RATE-HIKE-COMPLACENCY"

# ── Parameters (module-level so walk-forward can monkey-patch) ───────────────
VIX_MAX = 16.0              # Complacency floor: VIX <= this
NEAR_ATH_PCT = 0.02          # SPY within this % of 60-day high
SPY_HIGH_LOOKBACK = 60       # Rolling high for "near ATH" check
YIELD_LOOKBACK = 20          # Days to measure yield rise
YIELD_RISE_BPS = 15.0        # 2yr yield must rise >= this many bps over YIELD_LOOKBACK
FLATTEN_BPS = 1.0            # 2s10s must flatten by at least this many bps
ATR_PERIOD = 14
ATR_STOP_MULT = 2.0
MIN_RR = 1.5
MAX_BARS_HELD = 10           # ~2 trading weeks

# Sector ETFs for the rotation
LONG_ETFS = ["XLP", "XLV", "XLU"]       # Defensive: staples, healthcare, utilities
SHORT_ETFS = ["XLK", "XLY"]              # Cyclical: tech, discretionary

_CACHE_DIR = Path.home() / ".hermes" / "market_data"

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
    """Load a cached parquet and return the close series."""
    p = _CACHE_DIR / f"{ticker}.parquet"
    if not p.exists():
        return pd.Series(dtype=float)
    df = pd.read_parquet(p)
    df.columns = [c.lower() for c in df.columns]
    df = df.sort_index()
    return df[col] if col in df.columns else df.iloc[:, 0]


def _load_regime() -> pd.Series:
    """Build a date-indexed boolean Series: rate_hike_complacency_active."""
    global _REGIME_SERIES, _REGIME_KEY
    key = (VIX_MAX, NEAR_ATH_PCT, SPY_HIGH_LOOKBACK, YIELD_LOOKBACK,
           YIELD_RISE_BPS, FLATTEN_BPS)
    if _REGIME_SERIES is not None and _REGIME_KEY == key:
        return _REGIME_SERIES

    vix = _load_series("VIXINDEX")
    irx = _load_series("IRX")    # 13-week T-bill (proxy for short rate)
    tnx = _load_series("TNX")    # 10-year Treasury yield
    spy = _load_series("SPY")

    if vix.empty or spy.empty:
        _REGIME_SERIES = pd.Series(False, index=pd.DatetimeIndex([]))
        _REGIME_KEY = key
        return _REGIME_SERIES

    # Align all to VIX dates (the most constrained)
    common_idx = vix.index
    if not irx.empty:
        common_idx = common_idx.intersection(irx.index)
    if not tnx.empty:
        common_idx = common_idx.intersection(tnx.index)
    common_idx = common_idx.intersection(spy.index)

    vix = vix.reindex(common_idx)
    spy = spy.reindex(common_idx)

    # Condition 1: VIX <= VIX_MAX
    cond_vix = vix <= VIX_MAX

    # Condition 2: SPY within NEAR_ATH_PCT of 60-day high
    spy_high = spy.rolling(SPY_HIGH_LOOKBACK, min_periods=SPY_HIGH_LOOKBACK).max()
    spy_near_ath = (spy >= spy_high * (1 - NEAR_ATH_PCT)) & spy_high.notna()

    # Conditions 3 & 4: yield-based (only if we have IRX and TNX)
    cond_yield = pd.Series(True, index=common_idx)  # default true if no yield data
    if not irx.empty and not tnx.empty:
        irx = irx.reindex(common_idx)
        tnx = tnx.reindex(common_idx)

        # Condition 3: 2yr yield (IRX proxy) risen >= YIELD_RISE_BPS over 20 days
        irx_change = irx - irx.shift(YIELD_LOOKBACK)
        cond_yield_rise = irx_change >= YIELD_RISE_BPS

        # Condition 4: 2s10s (TNX - IRX) has flattened (decreased) by >= FLATTEN_BPS
        spread = tnx - irx
        spread_change = spread - spread.shift(YIELD_LOOKBACK)
        cond_flatten = spread_change <= -FLATTEN_BPS

        # Both yield conditions must hold
        cond_yield = cond_yield_rise & cond_flatten & cond_yield_rise.notna()

    # All conditions
    active = cond_vix & spy_near_ath & cond_yield
    active = active.fillna(False)

    _REGIME_SERIES = active
    _REGIME_KEY = key
    return _REGIME_SERIES


def _simulate_exit(df, entry_idx, entry_price, stop_price, direction="long"):
    """Simulate exit: stop or time. Returns (exit_price, exit_reason, bars_held)."""
    closes = df["close"].values
    highs = df["high"].values
    lows = df["low"].values
    n = len(closes)

    for offset in range(1, MAX_BARS_HELD + 1):
        idx = entry_idx + offset
        if idx >= n:
            last_idx = min(entry_idx + offset - 1, n - 1)
            return closes[last_idx], "time", offset
        c = closes[idx]
        if direction == "long":
            if c <= stop_price:
                return c, "stop", offset
        else:
            if c >= stop_price:
                return c, "stop", offset
    exit_idx = min(entry_idx + MAX_BARS_HELD, n - 1)
    return closes[exit_idx], "time", MAX_BARS_HELD


def scan(data: dict) -> list:
    """
    Batch scanner. Takes the full stock data dict (must include sector ETFs).
    Returns signals for the defensive rotation trade.

    When the rate-hike-complacency regime is active, generates:
      - Long signals for XLP, XLV, XLU
      - Short signals for XLK, XLY
    """
    # Build regime series
    regime = _load_regime()
    if regime.empty:
        return []

    # Get all unique dates from the data dict
    all_dates = set()
    for df in data.values():
        all_dates.update(df.index)
    all_dates = sorted(all_dates)

    # Rebalance weekly (every 5 bars)
    rebalance_dates = all_dates[::5]

    signals = []

    for rebalance_idx, rebalance_date in enumerate(rebalance_dates):
        # Check regime
        if rebalance_date not in regime.index:
            # Find nearest prior date
            prior = regime[regime.index <= rebalance_date]
            if prior.empty:
                continue
            if not prior.iloc[-1]:
                continue
        elif not regime.loc[rebalance_date]:
            continue

        # Generate signals for sector ETFs
        for etf in LONG_ETFS:
            df = data.get(etf)
            if df is None or len(df) < ATR_PERIOD + 5:
                continue

            mask = df.index <= rebalance_date
            if mask.sum() < ATR_PERIOD + 5:
                continue

            df_slice = df[mask]
            entry_idx = len(df_slice) - 1
            entry_price = float(df_slice["close"].iloc[-1])

            atr = _compute_atr(df_slice["high"], df_slice["low"], df_slice["close"])
            atr_val = float(atr.iloc[-1])
            if atr_val <= 0:
                continue

            stop_price = entry_price - ATR_STOP_MULT * atr_val
            risk = entry_price - stop_price
            if risk <= 0:
                continue
            target_price = entry_price + MIN_RR * risk

            exit_price, exit_reason, bars_held = _simulate_exit(
                df, entry_idx, entry_price, stop_price, "long")
            realised_r = (exit_price - entry_price) / risk

            signals.append({
                "ticker": etf,
                "date": rebalance_date,
                "direction": "long",
                "entry_price": round(entry_price, 4),
                "stop_price": round(float(stop_price), 4),
                "target_price": round(float(target_price), 4),
                "exit_price": round(float(exit_price), 4),
                "exit_reason": exit_reason,
                "r_multiple": round(float(realised_r), 4),
                "bars_held": bars_held,
                "strategy_id": STRATEGY_ID,
                "subperiod": _subperiod(rebalance_date),
                "regime": "rate_hike_complacency",
            })

        for etf in SHORT_ETFS:
            df = data.get(etf)
            if df is None or len(df) < ATR_PERIOD + 5:
                continue

            mask = df.index <= rebalance_date
            if mask.sum() < ATR_PERIOD + 5:
                continue

            df_slice = df[mask]
            entry_idx = len(df_slice) - 1
            entry_price = float(df_slice["close"].iloc[-1])

            atr = _compute_atr(df_slice["high"], df_slice["low"], df_slice["close"])
            atr_val = float(atr.iloc[-1])
            if atr_val <= 0:
                continue

            stop_price = entry_price + ATR_STOP_MULT * atr_val
            risk = stop_price - entry_price
            if risk <= 0:
                continue
            target_price = entry_price - MIN_RR * risk

            exit_price, exit_reason, bars_held = _simulate_exit(
                df, entry_idx, entry_price, stop_price, "short")
            realised_r = (entry_price - exit_price) / risk

            signals.append({
                "ticker": etf,
                "date": rebalance_date,
                "direction": "short",
                "entry_price": round(entry_price, 4),
                "stop_price": round(float(stop_price), 4),
                "target_price": round(float(target_price), 4),
                "exit_price": round(float(exit_price), 4),
                "exit_reason": exit_reason,
                "r_multiple": round(float(realised_r), 4),
                "bars_held": bars_held,
                "strategy_id": STRATEGY_ID,
                "subperiod": _subperiod(rebalance_date),
                "regime": "rate_hike_complacency",
            })

    return signals


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from fetch_data import load_all

    print("Loading stock data...")
    stocks = load_all()
    print(f"  {len(stocks)} tickers loaded")

    print("\nRunning STR-RHC rate-hike complacency divergence...")
    signals = scan(stocks)

    if not signals:
        print("No signals generated (regime may not have triggered historically).")
        sys.exit(0)

    r_values = [s["r_multiple"] for s in signals]
    long_sigs = [s for s in signals if s["direction"] == "long"]
    short_sigs = [s for s in signals if s["direction"] == "short"]
    wins = [s for s in signals if s["r_multiple"] > 0]

    avg_r = np.mean(r_values)
    win_rate = len(wins) / len(signals)

    print(f"\nSTR-RHC Phase 1A Results:")
    print(f"  Signals: {len(signals)} ({len(long_sigs)} long, {len(short_sigs)} short)")
    print(f"  Avg R: {avg_r:+.4f}")
    print(f"  Win rate: {win_rate:.1%}")

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
