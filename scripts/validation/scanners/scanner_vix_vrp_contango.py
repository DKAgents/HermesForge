#!/usr/bin/env python3
"""
scanner_vix_vrp_contango.py
===========================
HermesForge Phase 1A — VIX Term-Structure Contango Breakout (equity long).

Edge candidate: CAND-20260816-vix-contango-persistence
Source hypothesis: 06-Strategies candidate — "Persistent VIX term-structure
contango (IVTS < 0.85 sustained >= 60 days) → equity upside regime. VRP is
one of the most documented anomalies."

Signal Rules:
  Regime gate (computed once from cached ^VIX and ^VIX3M daily series):
    - IVTS  = VIX_spot / VIX3M      (term-structure ratio; <1 = contango)
    - Contango-active day:  IVTS <= IVTS_MAX  AND  VIX_spot <= VIX_MAX
    - "Persistent" requirement: contango-active has held for >= MIN_CONTANGO_DAYS
      consecutive trading days ending on the signal day (captures the
      "90+ days of contango" persistence angle from the candidate).
    The precomputed boolean series `contango_active` is reindexed to each
    ticker's trading dates (ffill) — same pattern as scanner_h's regime load.

  Per-ticker entry (all required, on the signal day i):
    - close > 20-day rolling max of prior closes (20-day breakout, excl. today)
    - volume > 1.2 * 20-day average volume (volume expansion confirms breakout)
    - close > 50-SMA (intermediate trend agreement)
    - ATR% of price <= MAX_ATR_PCT (avoid illiquid/high-vol names)
    - Regime gate: contango_active[i] == True

  Risk/reward & exit (forward-scan from entry bar, max MAX_BARS_HELD bars):
    - entry  = close[i]
    - stop   = min(low[i], 20-SMA[i]) - STOP_BUFFER_ATR * ATR(i)   (below 20MA)
    - target = entry + MIN_RR * risk
    - exit 'target' / 'stop' / 'time'

Dependencies: pandas, numpy. VIX/VIX3M loaded from local parquet cache
(~/.hermes/market_data/VIXINDEX.parquet, VIX3M.parquet). If VIX3M is missing
the scanner falls back to a VRP proxy (VIX vs 20d realized vol of SPY) so it
still runs — the contango requirement is then approximated by VRP > VRP_MIN
sustained >= MIN_CONTANGO_DAYS.

Survivorship-bias caveat: universe is current S&P constituents (ADR-004).
Transaction costs are NOT modeled here — Phase 1A is frictionless; the
walk-forward stage applies spread+commission+gap costs.
"""

import numpy as np
import pandas as pd
from pathlib import Path

STRATEGY_ID = "STR-20260816-VIX-VRP-CONTANGO-BREAKOUT"

# ── Parameters (module-level so walk-forward can monkey-patch) ────────────────
IVTS_MAX = 0.92          # contango threshold (VIX/VIX3M <= this = contango)
VIX_MAX = 20.0           # only trade when spot VIX calm (≤20)
PERSIST_WINDOW = 90      # rolling window (days) for persistence fraction
MIN_PERSIST_FRAC = 0.6   # contango must have held >= this fraction of the window
VRP_MIN = 1.0            # fallback-proxy VRP (vol points) for contango (no VIX3M)
BREAKOUT_LOOKBACK = 20
VOL_AVG_PERIOD = 20
MA_TREND = 50
MIN_RR = 2.0
STOP_BUFFER_ATR = 0.5
MAX_ATR_PCT = 0.08
ATR_PERIOD = 14
MAX_BARS_HELD = 12
MA_SLOW = 200

_SPY_CACHE = Path.home() / ".hermes" / "market_data" / "SPY.parquet"
_VIX_CACHE = Path.home() / ".hermes" / "market_data" / "VIXINDEX.parquet"
_VIX3M_CACHE = Path.home() / ".hermes" / "market_data" / "VIX3M.parquet"

_REGIME_SERIES: "pd.Series | None" = None  # contango_active indexed by date
_REGIME_KEY = None  # tuple of params used to build _REGIME_SERIES


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


def _load_contango_regime() -> pd.Series:
    """Build a date-indexed boolean Series: contango_active (persisted).

    Rebuilds when any regime-defining parameter changes (walk-forward
    monkey-patches these between runs), so the cache never serves a stale
    regime built under different IVTS/VIX/persistence thresholds.
    """
    global _REGIME_SERIES, _REGIME_KEY
    key = (IVTS_MAX, VIX_MAX, PERSIST_WINDOW, MIN_PERSIST_FRAC)
    if _REGIME_SERIES is not None and _REGIME_KEY == key:
        return _REGIME_SERIES

    vix = pd.read_parquet(_VIX_CACHE)
    vix.columns = [c.lower() for c in vix.columns]
    vix = vix.sort_index()
    vix_close = vix["close"]

    if _VIX3M_CACHE.exists():
        vix3m = pd.read_parquet(_VIX3M_CACHE)
        vix3m.columns = [c.lower() for c in vix3m.columns]
        vix3m = vix3m.sort_index()
        vix3m_close = vix3m["close"].reindex(vix_close.index).ffill()
        ivts = (vix_close / vix3m_close.replace(0, np.nan))
        contango_day = (ivts <= IVTS_MAX) & (vix_close <= VIX_MAX) & ivts.notna()
    else:
        # Fallback: VRP proxy = VIX - annualized 20d realized vol of SPY
        spy = pd.read_parquet(_SPY_CACHE)
        spy.columns = [c.lower() for c in spy.columns]
        spy = spy.sort_index()
        ret = spy["close"].pct_change()
        rv = ret.rolling(20).std() * np.sqrt(252)
        rv = rv.reindex(vix_close.index).ffill()
        vrp = vix_close - rv
        contango_day = (vrp >= VRP_MIN) & (vix_close <= VIX_MAX) & vrp.notna()

    # Persistence: contango has been the norm recently — rolling fraction of
    # contango-day over the last PERSIST_WINDOW days >= MIN_PERSIST_FRAC, AND
    # today is itself a contango day. (A rolling fraction, not a strict all-N-
    # days streak, because VIX spikes would otherwise break the streak and
    # kill the regime even when contango is the dominant state.)
    roll_frac = contango_day.rolling(PERSIST_WINDOW, min_periods=PERSIST_WINDOW).mean()
    contango_active = contango_day & (roll_frac >= MIN_PERSIST_FRAC)

    _REGIME_SERIES = contango_active.fillna(False)
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


def scan(df: pd.DataFrame, ticker: str) -> list:
    """Per-ticker scan for VIX-contango-gated 20-day breakouts (long only)."""
    if ticker in ("SPY", "VIXINDEX", "VIX3M", "^VIX", "^VIX3M"):
        return []

    df = df.copy()
    df.sort_index(inplace=True)
    if len(df) < max(MA_SLOW, BREAKOUT_LOOKBACK, VOL_AVG_PERIOD, ATR_PERIOD) + 10:
        return []

    close = df["close"]
    high = df["high"]
    low = df["low"]
    volume = df["volume"] if "volume" in df.columns else None

    atr = _compute_atr(high, low, close)
    ma50 = close.rolling(MA_TREND, min_periods=MA_TREND).mean()
    vol_avg = volume.rolling(VOL_AVG_PERIOD, min_periods=VOL_AVG_PERIOD).mean() if volume is not None else None
    # 20-day breakout: today's close > max of prior 20 closes (excluding today)
    prior_max = close.shift(1).rolling(BREAKOUT_LOOKBACK, min_periods=BREAKOUT_LOOKBACK).max()

    regime = _load_contango_regime()
    regime_aligned = regime.reindex(df.index).ffill().fillna(False)

    min_start = max(MA_SLOW, ATR_PERIOD, VOL_AVG_PERIOD, BREAKOUT_LOOKBACK) + 1
    close_arr = close.values
    high_arr = high.values
    low_arr = low.values
    ma50_arr = ma50.values
    atr_arr = atr.values
    vol_arr = volume.values if volume is not None else None
    vol_avg_arr = vol_avg.values if vol_avg is not None else None
    prior_max_arr = prior_max.values
    reg_arr = regime_aligned.values
    dates = df.index

    signals = []
    n = len(df)
    for i in range(min_start, n):
        if not bool(reg_arr[i]):
            continue
        if np.isnan(prior_max_arr[i]) or close_arr[i] <= prior_max_arr[i]:
            continue
        if np.isnan(ma50_arr[i]) or close_arr[i] <= ma50_arr[i]:
            continue
        if np.isnan(atr_arr[i]) or atr_arr[i] <= 0:
            continue
        if atr_arr[i] / close_arr[i] > MAX_ATR_PCT:
            continue
        if vol_arr is None or vol_avg_arr is None:
            continue
        if np.isnan(vol_avg_arr[i]) or vol_avg_arr[i] <= 0:
            continue
        if vol_arr[i] < 1.2 * vol_avg_arr[i]:
            continue

        entry_price = close_arr[i]
        stop_price = min(low_arr[i], ma50_arr[i]) - STOP_BUFFER_ATR * atr_arr[i]
        risk = entry_price - stop_price
        if risk <= 0 or risk / entry_price < 0.003:
            continue
        target_price = entry_price + MIN_RR * risk

        exit_price, exit_reason, bars_held = _simulate_exit(
            df, i, entry_price, stop_price, target_price, "long")
        realised_r = (exit_price - entry_price) / risk

        signals.append({
            "ticker": ticker,
            "date": dates[i],
            "direction": "long",
            "entry_price": round(float(entry_price), 4),
            "stop_price": round(float(stop_price), 4),
            "target_price": round(float(target_price), 4),
            "exit_price": round(float(exit_price), 4),
            "exit_reason": exit_reason,
            "r_multiple": round(float(realised_r), 4),
            "bars_held": bars_held,
            "subperiod": _subperiod(dates[i]),
            "strategy_id": STRATEGY_ID,
        })
    return signals


if __name__ == "__main__":
    import sys
    data_path = Path.home() / ".hermes" / "market_data" / "AAPL.parquet"
    if not data_path.exists():
        print(f"[ERROR] {data_path} not found")
        sys.exit(1)
    d = pd.read_parquet(data_path)
    d.columns = [c.lower() for c in d.columns]
    sigs = scan(d, "AAPL")
    print(f"AAPL signals: {len(sigs)}")
