#!/usr/bin/env python3
"""
regime_filter.py — Market regime detection from cached data sources.

Replaces the former hardcoded JSON stub with a real module that:
  - Reads VIX, DXY, TNX, SPY, Fear&Greed, stock breadth, crypto correlation
    from cached parquet files
  - Computes a weighted regime classification with hard overrides
  - Exposes get_regime() and tag_signal() for strategy selection
  - Handles missing/stale data gracefully (never raises)
  - Is look-ahead-free (supports as_of parameter for backtesting)

Usage:
    from regime_filter import get_regime, tag_signal
    regime = get_regime()
    tag_signal(signal_dict, regime)

    python3 regime_filter.py              # print regime as JSON
    python3 regime_filter.py --as-of 2026-06-01  # historical regime
"""

import json
import os
import pathlib
import random
import time
from datetime import datetime, timezone, timedelta

# --------------------------------------------------------------------------- #
# numpy / pandas import guard (works in any venv)
# --------------------------------------------------------------------------- #
try:
    import numpy as np
    import pandas as pd
    HAS_NUMPY = True
except ImportError:  # pragma: no cover - fallback path
    HAS_NUMPY = False
    np = None
    pd = None

# Pure-Python fallbacks (used only when numpy/pandas unavailable)
import math
import statistics


# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #
MARKET_DATA_DIR = pathlib.Path.home() / ".hermes" / "market_data"
CRYPTO_DATA_DIR = MARKET_DATA_DIR / "6h"
STALE_THRESHOLD_HOURS = 24
BREADTH_SAMPLE_SIZE = 100

# Fixed seed for breadth sampling (reproducible within a session)
_BREADTH_SEED = 42

# Component weights (must sum to 1.0)
COMPONENT_WEIGHTS = {
    "vix": 0.20,
    "breadth": 0.20,
    "spy_trend": 0.20,
    "dxy": 0.15,
    "fear_greed": 0.10,
    "correlation": 0.10,
    "yields": 0.05,
}

# Files to exclude from breadth sample (macro / index files, not individual stocks)
_MACRO_STEMS = {"VIXINDEX", "VIX3M", "DXY", "DX-Y.NYB", "TNX", "^TNX",
                "SPY", "fear_greed", "BTC", "ETH", "USDC", "USDT"}

# Breadth session cache (TTL 5 min)
_breadth_cache = {"value": None, "timestamp": 0.0, "as_of_key": None}
_BREADTH_CACHE_TTL = 300  # seconds


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _has_pd():
    return HAS_NUMPY and pd is not None


def _safe_sma(values, n):
    """Simple moving average over last n values (pure python or numpy)."""
    if not values or n <= 0:
        return None
    window = values[-n:]
    if len(window) < n:
        return None
    if HAS_NUMPY:
        return float(np.mean(window))
    return sum(window) / n


def _pearson_corr(x, y):
    """Pearson correlation of two equal-length sequences."""
    n = min(len(x), len(y))
    if n < 3:
        return None
    x, y = x[-n:], y[-n:]
    if HAS_NUMPY:
        if np.std(x) == 0 or np.std(y) == 0:
            return 0.0
        r = float(np.corrcoef(x, y)[0, 1])
        if math.isnan(r):
            return 0.0
        return r
    # Pure-Python fallback (Python 3.10+)
    try:
        return float(statistics.correlation(x, y))
    except Exception:
        sx = statistics.stdev(x)
        sy = statistics.stdev(y)
        if sx == 0 or sy == 0:
            return 0.0
        mx = statistics.mean(x)
        my = statistics.mean(y)
        cov = sum((a - mx) * (b - my) for a, b in zip(x, y)) / (n - 1)
        return cov / (sx * sy)


def _linear_slope(values):
    """Linear regression slope of a sequence (returns float or None)."""
    n = len(values)
    if n < 2:
        return 0.0
    if HAS_NUMPY:
        xs = np.arange(n, dtype=float)
        ys = np.array(values, dtype=float)
        slope = float(np.polyfit(xs, ys, 1)[0])
        if math.isnan(slope):
            return 0.0
        return slope
    # Pure python OLS slope
    xs = list(range(n))
    mx = sum(xs) / n
    my = sum(values) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, values))
    den = sum((x - mx) ** 2 for x in xs)
    if den == 0:
        return 0.0
    return num / den


def _load_parquet_as_of(path, as_of=None, columns=None):
    """
    Load a parquet file, optionally truncating to as_of date.
    Returns a pandas DataFrame (with DatetimeIndex) or None on failure.
    """
    if not _has_pd():
        return None
    try:
        df = pd.read_parquet(path, columns=columns)
    except Exception:
        return None
    if df is None or df.empty:
        return None
    # Ensure we have a DatetimeIndex
    idx = df.index
    if not isinstance(idx, pd.DatetimeIndex):
        # Try to use a date-like column
        for col in ("Date", "date", "timestamp"):
            if col in df.columns:
                try:
                    df = df.set_index(col)
                    df.index = pd.to_datetime(df.index)
                except Exception:
                    pass
                break
        if not isinstance(df.index, pd.DatetimeIndex):
            try:
                df.index = pd.to_datetime(df.index)
            except Exception:
                return None
    if as_of is not None:
        try:
            as_of_ts = pd.Timestamp(as_of)
            df = df[df.index <= as_of_ts]
        except Exception:
            pass
    if df.empty:
        return None
    return df


def _get_close(path, as_of=None, n_tail=None):
    """Read the 'close' column from a parquet file, truncated to as_of."""
    df = _load_parquet_as_of(path, as_of=as_of, columns=["close"])
    if df is None:
        return None
    if "close" not in df.columns:
        # try Close (capitalized fallback)
        for c in df.columns:
            if c.lower() == "close":
                df = df.rename(columns={c: "close"})
                break
    if "close" not in df.columns:
        return None
    if n_tail is not None:
        df = df.tail(n_tail)
    return df["close"]


def _last_date(path):
    """Return the last date in a parquet file (Timestamp) or None."""
    # Try close column projection first (fast), then fall back to any columns.
    df = _load_parquet_as_of(path, columns=["close"])
    if df is None:
        df = _load_parquet_as_of(path)
    if df is None:
        return None
    return df.index[-1]


def _check_freshness(path, as_of=None):
    """
    Returns (freshness_label, confidence_penalty).
      "fresh":       last bar within 24h of as_of/now -> penalty = 1.0
      "stale":       24h-72h -> penalty = 0.8
      "very_stale":  72h-7d -> penalty = 0.5
      "unavailable": file missing or >7d -> penalty = 0.3
    """
    if not path.exists():
        return ("unavailable", 0.3)
    last = _last_date(path)
    if last is None:
        return ("unavailable", 0.3)
    ref = pd.Timestamp(as_of) if (as_of and _has_pd()) else pd.Timestamp.now()
    if _has_pd():
        try:
            age = ref - last
        except Exception:
            return ("unavailable", 0.3)
        hours = age.total_seconds() / 3600.0
    else:
        # crude fallback
        hours = 999.0
    if hours < 24:
        return ("fresh", 1.0)
    elif hours < 72:
        return ("stale", 0.8)
    if hours < 168:
        return ("very_stale", 0.5)
    return ("unavailable", 0.3)


# --------------------------------------------------------------------------- #
# Component: VIX
# --------------------------------------------------------------------------- #
def _compute_vix(as_of=None):
    path = MARKET_DATA_DIR / "VIXINDEX.parquet"
    vix3m_path = MARKET_DATA_DIR / "VIX3M.parquet"
    result = {
        "current": 0.0, "regime": "unknown", "change_5d": 0.0,
        "change_pct_5d": 0.0, "term_structure": "flat", "vix_3m": None,
        "available": False, "score": 0.5, "freshness": "unavailable",
        "sharp_rise": False,
    }
    s = _get_close(path, as_of=as_of)
    if s is None or len(s) == 0:
        return result
    current = float(s.iloc[-1])
    result["current"] = current
    result["available"] = True
    result["freshness"], _ = _check_freshness(path, as_of)
    # 5-day change
    if len(s) >= 6:
        prev = float(s.iloc[-6])
        result["change_5d"] = current - prev
        result["change_pct_5d"] = ((current / prev) - 1) * 100 if prev != 0 else 0.0
    # Sub-regime
    if current < 18:
        result["regime"] = "low"
        result["score"] = 1.0
    elif current < 25:
        result["regime"] = "normal"
        result["score"] = 0.5
    else:
        result["regime"] = "high"
        result["score"] = 0.0
    # Sharp rise detection
    if result["change_pct_5d"] > 25:
        result["sharp_rise"] = True
    # Term structure
    vix3m = _get_close(vix3m_path, as_of=as_of)
    if vix3m is not None and len(vix3m) > 0:
        v3 = float(vix3m.iloc[-1])
        result["vix_3m"] = v3
        if v3 > current * 1.05:
            result["term_structure"] = "contango"
        elif v3 < current * 0.95:
            result["term_structure"] = "backwardation"
        else:
            result["term_structure"] = "flat"
    return result


# --------------------------------------------------------------------------- #
# Component: DXY
# --------------------------------------------------------------------------- #
def _compute_dxy(as_of=None):
    # Try DXY.parquet first, then DX-Y.NYB.parquet
    path = MARKET_DATA_DIR / "DXY.parquet"
    if not path.exists():
        path = MARKET_DATA_DIR / "DX-Y.NYB.parquet"
    result = {
        "current": 0.0, "trend": "unknown", "change_5d": 0.0,
        "regime": "neutral", "available": False, "score": 0.5,
        "freshness": "unavailable", "slope_20d": 0.0,
    }
    s = _get_close(path, as_of=as_of)
    if s is None:
        return result
    current = float(s.iloc[-1])
    result["current"] = current
    result["available"] = True
    result["freshness"], _ = _check_freshness(path, as_of)
    if len(s) >= 6:
        result["change_5d"] = current - float(s.iloc[-6])
    # 20-day slope
    window = [float(x) for x in s.tail(20)]
    slope = _linear_slope(window)
    result["slope_20d"] = slope
    if slope < -0.02:
        result["trend"] = "falling"
        result["regime"] = "dollar_weak"
        result["score"] = 0.8
    elif slope > 0.02:
        result["trend"] = "rising"
        result["regime"] = "dollar_strong"
        result["score"] = 0.2
    else:
        result["trend"] = "flat"
        result["regime"] = "neutral"
        result["score"] = 0.5
    return result


# --------------------------------------------------------------------------- #
# Component: Yields (TNX)
# --------------------------------------------------------------------------- #
def _compute_yields(as_of=None):
    # Try TNX.parquet first, then ^TNX.parquet
    path = MARKET_DATA_DIR / "TNX.parquet"
    if not path.exists():
        path = MARKET_DATA_DIR / "^TNX.parquet"
    result = {
        "t10y": 0.0, "t10y_trend": "flat", "yield_curve_status": "partial_data",
        "available": False, "score": 0.5, "freshness": "unavailable",
    }
    s = _get_close(path, as_of=as_of)
    if s is None:
        return result
    t10 = float(s.iloc[-1])
    result["t10y"] = t10
    result["available"] = True
    result["freshness"], _ = _check_freshness(path, as_of)
    window = [float(x) for x in s.tail(20)]
    slope = _linear_slope(window)
    result["t10y_trend"] = "rising" if slope > 0 else ("falling" if slope < 0 else "flat")
    if t10 > 4.5 and slope > 0:
        result["yield_curve_status"] = "caution"
        result["score"] = 0.3
    elif t10 < 3.5:
        result["yield_curve_status"] = "accommodative"
        result["score"] = 0.8
    else:
        result["yield_curve_status"] = "normal"
        result["score"] = 0.5
    return result


# --------------------------------------------------------------------------- #
# Component: Fear & Greed
# --------------------------------------------------------------------------- #
def _compute_fear_greed(as_of=None):
    path = MARKET_DATA_DIR / "fear_greed.parquet"
    result = {
        "value": 50, "classification": "Neutral", "regime": "neutral",
        "available": False, "score": 0.5, "freshness": "unavailable",
    }
    if not _has_pd() or not path.exists():
        return result
    try:
        df = pd.read_parquet(path)
    except Exception:
        return result
    if df is None or df.empty:
        return result
    # fear_greed has 'date','value','classification' columns, no DatetimeIndex
    for col in ("date", "Date", "timestamp"):
        if col in df.columns:
            try:
                df = df.set_index(col)
                df.index = pd.to_datetime(df.index)
            except Exception:
                pass
            break
    if not isinstance(df.index, pd.DatetimeIndex):
        try:
            df.index = pd.to_datetime(df.index)
        except Exception:
            return result
    if as_of is not None:
        try:
            df = df[df.index <= pd.Timestamp(as_of)]
        except Exception:
            pass
    if df.empty:
        return result
    result["available"] = True
    result["freshness"], _ = _check_freshness(path, as_of)
    val_col = "value" if "value" in df.columns else df.columns[0]
    cls_col = "classification" if "classification" in df.columns else None
    value = float(df[val_col].iloc[-1])
    result["value"] = value
    if cls_col:
        result["classification"] = str(df[cls_col].iloc[-1])
    # Sub-regime
    if value < 25:
        result["regime"] = "extreme_fear"
        result["score"] = 0.3
    elif value < 45:
        result["regime"] = "fear"
        result["score"] = 0.5
    elif value < 55:
        result["regime"] = "neutral"
        result["score"] = 0.5
    elif value < 75:
        result["regime"] = "greed"
        result["score"] = 0.7
    else:
        result["regime"] = "extreme_greed"
        result["score"] = 0.2
    return result


# --------------------------------------------------------------------------- #
# Component: SPY Trend
# --------------------------------------------------------------------------- #
def _compute_spy_trend(as_of=None):
    path = MARKET_DATA_DIR / "SPY.parquet"
    result = {
        "close": 0.0, "above_50ma": False, "above_200ma": False,
        "ma_50": None, "ma_200": None, "trend": "unknown",
        "available": False, "score": 0.5, "freshness": "unavailable",
    }
    s = _get_close(path, as_of=as_of)
    if s is None:
        return result
    closes = [float(x) for x in s]
    result["close"] = closes[-1]
    result["available"] = True
    result["freshness"], _ = _check_freshness(path, as_of)
    ma50 = _safe_sma(closes, 50)
    ma200 = _safe_sma(closes, 200)
    result["ma_50"] = ma50
    result["ma_200"] = ma200
    above_50 = ma50 is not None and closes[-1] > ma50
    above_200 = ma200 is not None and closes[-1] > ma200
    result["above_50ma"] = bool(above_50)
    result["above_200ma"] = bool(above_200)
    if above_50 and above_200:
        result["trend"] = "uptrend"
        result["score"] = 1.0
    elif not above_50 and not above_200:
        result["trend"] = "downtrend"
        result["score"] = 0.0
    elif above_50 and not above_200:
        result["trend"] = "recovering"
        result["score"] = 0.6
    else:
        result["trend"] = "pullback"
        result["score"] = 0.4
    return result


# --------------------------------------------------------------------------- #
# Component: Breadth (100-stock random sample)
# --------------------------------------------------------------------------- #
def _compute_breadth(as_of=None, spy_up=None):
    result = {
        "pct_above_50ma": 50.0, "advancing_pct": 50.0, "divergence": "none",
        "sample_size": 0, "available": False, "score": 0.5,
        "freshness": "unavailable",
    }
    if not _has_pd():
        return result
    # Cache key by as_of so look-ahead-free calls don't serve a cached current call
    cache_key = as_of if as_of else "now"
    if (_breadth_cache["value"] is not None and
            _breadth_cache["as_of_key"] == cache_key and
            time.time() - _breadth_cache["timestamp"] < _BREADTH_CACHE_TTL):
        return _breadth_cache["value"]

    try:
        all_files = sorted(MARKET_DATA_DIR.glob("*.parquet"))
    except Exception:
        return result
    stock_files = [f for f in all_files
                   if f.stem not in _MACRO_STEMS and not f.stem.startswith("^")]
    if not stock_files:
        return result
    sample = random.Random(_BREADTH_SEED).sample(
        stock_files, min(BREADTH_SAMPLE_SIZE, len(stock_files)))
    above_count = 0
    advancing_count = 0
    used = 0
    for p in sample:
        try:
            df = pd.read_parquet(p, columns=["close"])
        except Exception:
            continue
        if df is None or df.empty or "close" not in df.columns:
            continue
        if not isinstance(df.index, pd.DatetimeIndex):
            try:
                df.index = pd.to_datetime(df.index)
            except Exception:
                continue
        if as_of is not None:
            try:
                df = df[df.index <= pd.Timestamp(as_of)]
            except Exception:
                pass
        if df.empty or len(df) < 2:
            continue
        closes = df["close"].astype(float)
        used += 1
        last = float(closes.iloc[-1])
        prev = float(closes.iloc[-2])
        if last > prev:
            advancing_count += 1
        if len(closes) >= 51:
            ma50 = float(closes.iloc[-51:].mean())
        else:
            ma50 = float(closes.mean()) if len(closes) > 0 else last
        if last > ma50:
            above_count += 1
    if used == 0:
        return result
    pct_above = (above_count / used) * 100.0
    advancing = (advancing_count / used) * 100.0
    result["pct_above_50ma"] = pct_above
    result["advancing_pct"] = advancing
    result["sample_size"] = used
    result["available"] = True
    result["freshness"] = "fresh"
    # Divergence detection (spy_up is set by caller from SPY data)
    if spy_up is True and advancing < 45:
        result["divergence"] = "bearish"
    elif spy_up is False and advancing > 55:
        result["divergence"] = "bullish"
    # Sub-regime
    if pct_above > 70 and advancing > 60:
        result["score"] = 0.9
    elif pct_above < 30 and advancing < 40:
        result["score"] = 0.1
    else:
        result["score"] = 0.5
    # Cache it
    _breadth_cache["value"] = result
    _breadth_cache["timestamp"] = time.time()
    _breadth_cache["as_of_key"] = cache_key
    return result


# --------------------------------------------------------------------------- #
# Component: Cross-Asset Correlation
# --------------------------------------------------------------------------- #
def _compute_correlation(as_of=None):
    result = {
        "correlation_regime": "normal", "stock_crypto_corr_30d": None,
        "stock_internal_corr_30d": None, "description": "Moderate cross-asset correlation",
        "available": False, "score": 0.5, "freshness": "unavailable",
    }
    if not _has_pd():
        return result
    # SPY daily returns (last 31)
    spy_s = _get_close(MARKET_DATA_DIR / "SPY.parquet", as_of=as_of)
    if spy_s is None or len(spy_s) < 2:
        return result
    spy_ret = [float(spy_s.iloc[i] / spy_s.iloc[i - 1] - 1)
              for i in range(1, len(spy_s))][-31:]
    # BTC 6h resample to daily
    btc_path = CRYPTO_DATA_DIR / "BTC.parquet"
    btc_corr = None
    if btc_path.exists():
        btc_df = _load_parquet_as_of(btc_path, as_of=as_of, columns=["close"])
        if btc_df is not None and len(btc_df) >= 2:
            btc_daily = btc_df["close"].astype(float).resample("1D").last().dropna()
            btc_ret = [float(btc_daily.iloc[i] / btc_daily.iloc[i - 1] - 1)
                      for i in range(1, len(btc_daily))][-31:]
            if len(btc_ret) >= 5:
                btc_corr = _pearson_corr(spy_ret, btc_ret)
    # Check BTC freshness — if last BTC date > 30 days before as_of/now, skip
    btc_fresh = False
    if btc_path.exists():
        b_last = _last_date(btc_path)
        if b_last is not None and btc_corr is not None:
            ref = pd.Timestamp(as_of) if as_of else pd.Timestamp.now()
            age_days = (ref - b_last).days if ref is not None and b_last is not None else 999
            btc_fresh = age_days < 30
    if btc_corr is not None and btc_fresh:
        result["stock_crypto_corr_30d"] = btc_corr
        result["available"] = True
        result["freshness"] = "fresh" if btc_fresh else "stale"
    # Stock internal correlation: average pairwise of top 20 stocks
    internal_corr = None
    try:
        all_files = sorted(MARKET_DATA_DIR.glob("*.parquet"))
        stock_files = [f for f in all_files
                       if f.stem not in _MACRO_STEMS and not f.stem.startswith("^")]
        sample = random.Random(_BREADTH_SEED).sample(
            stock_files, min(20, len(stock_files)))
        rets = []
        for p in sample:
            df = pd.read_parquet(p, columns=["close"])
            if df is None or df.empty or "close" not in df.columns:
                continue
            if not isinstance(df.index, pd.DatetimeIndex):
                try:
                    df.index = pd.to_datetime(df.index)
                except Exception:
                    continue
            if as_of is not None:
                df = df[df.index <= pd.Timestamp(as_of)]
            if len(df) < 2:
                continue
            r = df["close"].astype(float).pct_change().dropna().tail(31)
            rets.append(r)
        if len(rets) >= 5:
            # align on common dates
            combined = pd.concat(rets, axis=1).dropna()
            if combined.shape[0] >= 5 and combined.shape[1] >= 2:
                corr_mat = combined.corr()
                # average of upper triangle (excluding diagonal)
                n_stocks = combined.shape[1]
                vals = []
                for i in range(n_stocks):
                    for j in range(i + 1, n_stocks):
                        v = corr_mat.iloc[i, j]
                        if not math.isnan(v):
                            vals.append(v)
                if vals:
                    internal_corr = sum(vals) / len(vals)
    except Exception:
        pass
    if internal_corr is not None:
        result["stock_internal_corr_30d"] = internal_corr
        result["available"] = True
    # Correlation regime
    sc = result["stock_crypto_corr_30d"]
    if sc is not None:
        if sc > 0.7:
            result["correlation_regime"] = "unified"
            result["score"] = 0.3
            result["description"] = "High stock-crypto correlation — unified market"
        elif sc < 0.3:
            result["correlation_regime"] = "diversified"
            result["score"] = 0.8
            result["description"] = "Low correlation — stock-picking environment"
        else:
            result["correlation_regime"] = "normal"
            result["score"] = 0.5
            result["description"] = "Moderate cross-asset correlation"
    else:
        result["correlation_regime"] = "normal"
        result["score"] = 0.5
        result["description"] = "Crypto correlation unavailable — assuming normal"
    return result


# --------------------------------------------------------------------------- #
# Component: Volatility Risk Premium
# --------------------------------------------------------------------------- #
def _compute_vrp(vix_current, spy_closes, as_of=None):
    result = {
        "vol_risk_premium": 0.0, "realized_vol_20d": 0.0,
        "interpretation": "Partial data", "available": False,
    }
    if spy_closes is None or len(spy_closes) < 21:
        return result
    rets = [float(spy_closes[i] / spy_closes[i - 1] - 1)
            for i in range(1, len(spy_closes))][-21:]
    if HAS_NUMPY:
        rv = float(np.std(rets, ddof=1)) * math.sqrt(252) * 100
    else:
        rv = statistics.stdev(rets) * math.sqrt(252) * 100 if len(rets) > 1 else 0.0
    result["realized_vol_20d"] = round(rv, 2)
    if vix_current and vix_current > 0:
        result["vol_risk_premium"] = round(vix_current - rv, 2)
        result["available"] = True
        vrp = vix_current - rv
        if vrp > 3:
            result["interpretation"] = "VIX well above realized — options pricing in fear (contrarian bullish)"
        elif vrp < -3:
            result["interpretation"] = "VIX below realized — options underpricing risk (cautious)"
        else:
            result["interpretation"] = "VIX near realized — normal"
    return result


# --------------------------------------------------------------------------- #
# Main: get_regime()
# --------------------------------------------------------------------------- #
def get_regime(as_of=None, force_refresh=False):
    """
    Determine the current market regime from cached parquet data.

    Never raises — on total failure, returns a degenerate neutral regime
    with confidence=0 and a 'data_unavailable' reason.
    """
    try:
        return _get_regime_impl(as_of, force_refresh)
    except Exception as e:
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "as_of": as_of,
            "overall": "neutral",
            "stock_regime": "neutral",
            "crypto_regime": "neutral",
            "confidence": 0.0,
            "data_freshness": "unavailable",
            "components": {},
            "reason": "data_unavailable",
            "error": str(e),
            "vix": {"current": 0, "regime": "unknown", "available": False},
            "dxy": {"current": 0, "trend": "unknown", "available": False},
            "fear_greed": {"value": 50, "classification": "Neutral", "available": False},
            "breadth": {"pct_above_50ma": 50, "advancing_pct": 50, "available": False},
            "spy_trend": {"trend": "unknown", "available": False},
            "correlation": {"correlation_regime": "normal", "available": False},
            "yields": {"t10y": 0, "available": False},
            "vol_risk_premium": {"vol_risk_premium": 0, "available": False},
            "put_call": {"total_ratio": 1.0, "available": False},
            "tvl": {"trend": "", "available": False},
            "stablecoin": {"trend": "", "available": False},
            "rotation": {"leading_sector": "", "lagging_sector": "", "available": False},
            "funding": {},
            "economic_events": [],
        }


def _get_regime_impl(as_of, force_refresh):
    # ------------------------------------------------------------------ #
    # Compute all components
    # ------------------------------------------------------------------ #
    vix = _compute_vix(as_of)
    dxy = _compute_dxy(as_of)
    yields = _compute_yields(as_of)
    fg = _compute_fear_greed(as_of)
    spy = _compute_spy_trend(as_of)
    corr = _compute_correlation(as_of)

    # SPY up/down for breadth divergence
    spy_up = None
    if spy["available"]:
        path = MARKET_DATA_DIR / "SPY.parquet"
        s = _get_close(path, as_of=as_of)
        if s is not None and len(s) >= 2:
            spy_up = float(s.iloc[-1]) > float(s.iloc[-2])
    breadth = _compute_breadth(as_of, spy_up=spy_up)

    # Vol risk premium
    spy_closes = None
    if spy["available"]:
        s = _get_close(MARKET_DATA_DIR / "SPY.parquet", as_of=as_of)
        if s is not None:
            spy_closes = [float(x) for x in s]
    vrp = _compute_vrp(vix["current"], spy_closes, as_of)

    # ------------------------------------------------------------------ #
    # Total failure check: if both critical sources (VIX + SPY) are missing,
    # return the degenerate neutral regime.
    # ------------------------------------------------------------------ #
    if not vix["available"] and not spy["available"]:
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "as_of": as_of,
            "overall": "neutral",
            "stock_regime": "neutral",
            "crypto_regime": "neutral",
            "confidence": 0.0,
            "data_freshness": "unavailable",
            "components": {},
            "reason": "data_unavailable",
            "error": "Critical data sources unavailable — VIX and SPY missing",
            "vix": {"current": 0, "regime": "unknown", "available": False},
            "dxy": {"current": 0, "trend": "unknown", "available": False},
            "yields": {"t10y": 0, "available": False},
            "fear_greed": {"value": 50, "classification": "Neutral",
                          "available": False},
            "breadth": {"pct_above_50ma": 50, "advancing_pct": 50,
                        "available": False, "sample_size": 0},
            "spy_trend": {"trend": "unknown", "available": False},
            "correlation": {"correlation_regime": "normal", "available": False},
            "vol_risk_premium": {"vol_risk_premium": 0, "available": False},
            "put_call": {"total_ratio": 1.0, "available": False},
            "tvl": {"trend": "", "available": False},
            "stablecoin": {"trend": "", "available": False},
            "rotation": {"leading_sector": "", "lagging_sector": "",
                         "available": False},
            "funding": {},
            "economic_events": [],
        }

    # ------------------------------------------------------------------ #
    # Assemble components dict for weighted scoring
    # ------------------------------------------------------------------ #
    components = {
        "vix": {"regime": vix["regime"], "score": vix["score"],
                "weight": COMPONENT_WEIGHTS["vix"], "available": vix["available"]},
        "breadth": {"regime": "strong" if breadth["score"] >= 0.8
                    else "weak" if breadth["score"] <= 0.2 else "mixed",
                    "score": breadth["score"],
                    "weight": COMPONENT_WEIGHTS["breadth"],
                    "available": breadth["available"]},
        "spy_trend": {"regime": spy["trend"], "score": spy["score"],
                      "weight": COMPONENT_WEIGHTS["spy_trend"],
                      "available": spy["available"]},
        "dxy": {"regime": dxy["regime"], "score": dxy["score"],
                "weight": COMPONENT_WEIGHTS["dxy"], "available": dxy["available"]},
        "fear_greed": {"regime": fg["regime"], "score": fg["score"],
                       "weight": COMPONENT_WEIGHTS["fear_greed"],
                       "available": fg["available"]},
        "correlation": {"regime": corr["correlation_regime"],
                        "score": corr["score"],
                        "weight": COMPONENT_WEIGHTS["correlation"],
                        "available": corr["available"]},
        "yields": {"regime": yields["yield_curve_status"],
                   "score": yields["score"],
                   "weight": COMPONENT_WEIGHTS["yields"],
                   "available": yields["available"]},
    }

    # ------------------------------------------------------------------ #
    # Weighted score (only from available components; renormalize weights)
    # ------------------------------------------------------------------ #
    total_weight_used = sum(c["weight"] for c in components.values()
                            if c["available"])
    if total_weight_used > 0:
        weighted_score = sum(c["score"] * c["weight"] for c in components.values()
                             if c["available"]) / total_weight_used
    else:
        weighted_score = 0.5

    # Count available components
    available_count = sum(1 for c in components.values() if c["available"])
    total_count = len(components)

    # Freshness penalties
    freshness_list = []
    freshness_labels = []
    for key in ("vix", "dxy", "yields", "fear_greed", "spy_trend"):
        comp = {"vix": vix, "dxy": dxy, "yields": yields,
                "fear_greed": fg, "spy_trend": spy}[key]
        if comp["available"]:
            f_label = comp.get("freshness", "fresh")
            freshness_labels.append(f_label)
            # map label to penalty
            pen = {"fresh": 1.0, "stale": 0.8, "very_stale": 0.5,
                   "unavailable": 0.3}.get(f_label, 0.5)
            freshness_list.append(pen)
    if breadth["available"]:
        freshness_list.append(1.0)
        freshness_labels.append("fresh")
    if corr["available"]:
        freshness_list.append({"fresh": 1.0, "stale": 0.8,
                               "very_stale": 0.5}.get(corr.get("freshness", "stale"), 0.8))
        freshness_labels.append(corr.get("freshness", "stale"))
    min_freshness = min(freshness_list) if freshness_list else 0.3

    # Overall freshness label
    if not freshness_labels:
        data_freshness = "unavailable"
    elif min(freshness_list) >= 1.0:
        data_freshness = "fresh"
    elif min(freshness_list) >= 0.8:
        data_freshness = "stale"
    elif min(freshness_list) >= 0.5:
        data_freshness = "very_stale"
    else:
        data_freshness = "unavailable"

    # ------------------------------------------------------------------ #
    # Hard override rules
    # ------------------------------------------------------------------ #
    override = None
    override_confidence = None
    vix_cur = vix["current"]
    vix_pct = vix["change_pct_5d"]
    sc_corr = corr["stock_crypto_corr_30d"]
    internal_corr = corr["stock_internal_corr_30d"]

    # OVERRIDE 1 — Risk-Off Crisis
    if vix["available"] and (vix_cur > 30 or (vix_cur > 25 and vix_pct > 30)):
        override = "risk_off"
        override_confidence = 0.9
    # OVERRIDE 2 — Sharp Volatility Spike (Caution)
    elif vix["available"] and vix_pct > 25 and vix_cur < 25:
        override = "caution"
        override_confidence = 0.7
    # OVERRIDE 3 — Unified Market
    elif sc_corr is not None and sc_corr > 0.8:
        override = "unified"
        override_confidence = 0.8
    # OVERRIDE 4 — Diversified Market
    elif sc_corr is not None and sc_corr < 0.2 and internal_corr is not None and internal_corr < 0.3:
        override = "diversified"
        override_confidence = 0.7

    # ------------------------------------------------------------------ #
    # Determine overall regime
    # ------------------------------------------------------------------ #
    if override is not None:
        overall = override
        base_confidence = override_confidence
    else:
        if weighted_score >= 0.70:
            overall = "risk_on"
        elif weighted_score >= 0.45:
            overall = "neutral"
        else:
            overall = "risk_off"
        base_confidence = weighted_score

    # ------------------------------------------------------------------ #
    # Confidence adjustment (completeness + freshness)
    # ------------------------------------------------------------------ #
    completeness_ratio = available_count / total_count if total_count > 0 else 0
    adjusted_conf = base_confidence * completeness_ratio
    final_conf = adjusted_conf * min_freshness
    if available_count < 3:
        final_conf = min(final_conf, 0.3)
    # clamp
    final_conf = max(0.0, min(1.0, final_conf))

    # ------------------------------------------------------------------ #
    # Stock vs Crypto regime
    # ------------------------------------------------------------------ #
    if overall in ("unified", "diversified"):
        if vix["available"] and vix_cur < 18 and spy["trend"] == "uptrend":
            stock_regime = "risk_on"
        elif vix["available"] and vix_cur > 25:
            stock_regime = "risk_off"
        else:
            stock_regime = "neutral"
    else:
        stock_regime = overall

    fg_val = fg["value"]
    if fg["available"] and fg_val < 25:
        crypto_regime = "caution"
    elif fg["available"] and fg_val > 75:
        crypto_regime = "caution"
    elif overall == "risk_on":
        crypto_regime = "risk_on"
    elif overall == "risk_off":
        crypto_regime = "risk_off"
    else:
        crypto_regime = "neutral"

    # ------------------------------------------------------------------ #
    # Build full result dict (satisfies all three callers)
    # ------------------------------------------------------------------ #
    result = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "as_of": as_of,
        "confidence": round(final_conf, 4),
        "data_freshness": data_freshness,
        "overall": overall,
        "stock_regime": stock_regime,
        "crypto_regime": crypto_regime,
        # VIX
        "vix": {
            "current": vix["current"],
            "regime": vix["regime"],
            "change_5d": round(vix["change_5d"], 4),
            "change_pct_5d": round(vix["change_pct_5d"], 2),
            "term_structure": vix["term_structure"],
            "vix_3m": vix["vix_3m"],
            "available": vix["available"],
        },
        # DXY
        "dxy": {
            "current": dxy["current"],
            "trend": dxy["trend"],
            "change_5d": round(dxy["change_5d"], 4),
            "regime": dxy["regime"],
            "available": dxy["available"],
        },
        # Yields
        "yields": {
            "t10y": yields["t10y"],
            "t10y_trend": yields["t10y_trend"],
            "yield_curve_status": yields["yield_curve_status"],
            "available": yields["available"],
        },
        # Fear & Greed
        "fear_greed": {
            "value": fg["value"],
            "classification": fg["classification"],
            "regime": fg["regime"],
            "available": fg["available"],
        },
        # Breadth
        "breadth": {
            "pct_above_50ma": round(breadth["pct_above_50ma"], 2),
            "advancing_pct": round(breadth["advancing_pct"], 2),
            "divergence": breadth["divergence"],
            "sample_size": breadth["sample_size"],
            "available": breadth["available"],
        },
        # SPY trend
        "spy_trend": {
            "close": spy["close"],
            "above_50ma": spy["above_50ma"],
            "above_200ma": spy["above_200ma"],
            "ma_50": round(spy["ma_50"], 4) if spy["ma_50"] is not None else None,
            "ma_200": round(spy["ma_200"], 4) if spy["ma_200"] is not None else None,
            "trend": spy["trend"],
            "available": spy["available"],
        },
        # Correlation
        "correlation": {
            "correlation_regime": corr["correlation_regime"],
            "stock_crypto_corr_30d": (round(sc_corr, 4)
                                     if sc_corr is not None else None),
            "stock_internal_corr_30d": (round(internal_corr, 4)
                                        if internal_corr is not None else None),
            "description": corr["description"],
            "available": corr["available"],
        },
        # VRP
        "vol_risk_premium": {
            "vol_risk_premium": vrp["vol_risk_premium"],
            "realized_vol_20d": vrp["realized_vol_20d"],
            "interpretation": vrp["interpretation"],
            "available": vrp["available"],
        },
        # Legacy placeholders (no free data source)
        "put_call": {"total_ratio": 1.0, "available": False},
        "tvl": {"trend": "", "available": False},
        "stablecoin": {"trend": "", "available": False},
        "rotation": {"leading_sector": "", "lagging_sector": "",
                     "available": False},
        "funding": {},
        "economic_events": [],
        # Components breakdown
        "components": components,
    }
    return result


# --------------------------------------------------------------------------- #
# tag_signal()
# --------------------------------------------------------------------------- #
def tag_signal(signal, regime=None):
    """
    Annotate a signal dict with regime context.

    MUTATES the signal dict in place AND returns it.
    """
    if regime is None:
        regime = get_regime()

    if not regime or regime.get("confidence", 0) == 0:
        signal["regime"] = "unknown"
        signal["regime_confidence"] = 0.0
        signal["regime_compatible"] = True  # don't block when unknown
        signal["regime_action"] = "run"
        signal["regime_risk_multiplier"] = 1.0
        signal["regime_tagged_at"] = datetime.now(timezone.utc).isoformat()
        return signal

    overall = regime.get("overall", "neutral")
    confidence = regime.get("confidence", 0.5)

    # Extract strategy prefix from signal ID
    strategy_id = signal.get("strategy_id", "")
    parts = strategy_id.split("-")
    strat_prefix = "-".join(parts[:2]) if len(parts) >= 2 else strategy_id

    # Look up strategy in registry (import locally to avoid circular imports)
    regime_best = []
    regime_avoid = []
    try:
        from regime_strategy_selector import STRATEGY_REGISTRY
        strat_info = STRATEGY_REGISTRY.get(strat_prefix, {})
        regime_best = strat_info.get("regime_best", [])
        regime_avoid = strat_info.get("regime_avoid", [])
    except Exception:
        pass

    # Build regime tags for matching
    regime_tags = [overall]
    corr = regime.get("correlation", {}).get("correlation_regime", "normal")
    if corr == "diversified":
        regime_tags.append("diversified")
    elif corr == "unified":
        regime_tags.append("unified")

    # Determine compatibility
    is_compatible = not any(r in regime_avoid for r in regime_tags)

    # Determine action and risk multiplier
    if any(r in regime_avoid for r in regime_tags):
        action = "suppress"
        risk_mult = 0.0
    elif any(r in regime_best for r in regime_tags):
        action = "boost"
        risk_mult = 1.5
    elif regime_best and not any(r in regime_best for r in regime_tags):
        # regime not in best and not in avoid -> reduce
        action = "reduce"
        risk_mult = 0.7
    else:
        action = "run"
        risk_mult = 1.0

    # Apply to signal dict (IN-PLACE mutation)
    signal["regime"] = overall
    signal["regime_confidence"] = confidence
    signal["regime_compatible"] = is_compatible
    signal["regime_action"] = action
    signal["regime_risk_multiplier"] = risk_mult
    signal["regime_tagged_at"] = datetime.now(timezone.utc).isoformat()

    return signal


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def _print_regime_human(regime):
    print(f"\nRegime Assessment — {regime.get('timestamp', '?')[:19]}")
    print(f"  Overall:    {regime.get('overall', '?')}")
    print(f"  Confidence: {regime.get('confidence', 0):.2f}")
    print(f"  Freshness:  {regime.get('data_freshness', '?')}")
    print(f"  Stock:      {regime.get('stock_regime', '?')}")
    print(f"  Crypto:     {regime.get('crypto_regime', '?')}")
    vix = regime.get("vix", {})
    print(f"  VIX:        {vix.get('current', 0):.2f} ({vix.get('regime', '?')}) "
          f"5d: {vix.get('change_pct_5d', 0):.1f}%")
    dxy = regime.get("dxy", {})
    print(f"  DXY:        {dxy.get('current', 0):.2f} ({dxy.get('trend', '?')})")
    fg = regime.get("fear_greed", {})
    print(f"  Fear&Greed: {fg.get('value', 50)} ({fg.get('classification', '?')})")
    br = regime.get("breadth", {})
    print(f"  Breadth:    {br.get('pct_above_50ma', 50):.1f}% > 50MA "
          f"(n={br.get('sample_size', 0)})")
    spy = regime.get("spy_trend", {})
    print(f"  SPY:        {spy.get('trend', '?')} "
          f"(>50ma={spy.get('above_50ma')}, >200ma={spy.get('above_200ma')})")
    corr = regime.get("correlation", {})
    print(f"  Corr:       {corr.get('correlation_regime', '?')} "
          f"(SPY-BTC={corr.get('stock_crypto_corr_30d')})")
    yld = regime.get("yields", {})
    print(f"  10Y:        {yld.get('t10y', 0):.3f}% ({yld.get('yield_curve_status', '?')})")
    vrp = regime.get("vol_risk_premium", {})
    print(f"  VRP:        {vrp.get('vol_risk_premium', 0):.1f} "
          f"(RV20d={vrp.get('realized_vol_20d', 0):.1f})")
    print()
    comps = regime.get("components", {})
    if comps:
        print("  Components:")
        for k, c in comps.items():
            av = "OK" if c.get("available") else "MISS"
            print(f"    {k:14s} regime={c.get('regime'):>12s} "
                  f"score={c.get('score'):.2f} w={c.get('weight'):.2f} [{av}]")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Market regime filter")
    ap.add_argument("--as-of", help="Historical date (YYYY-MM-DD)")
    ap.add_argument("--json", action="store_true", help="JSON output")
    args = ap.parse_args()

    regime = get_regime(as_of=args.as_of)
    if args.json:
        print(json.dumps(regime, indent=2, default=str))
    else:
        _print_regime_human(regime)
