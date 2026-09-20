#!/usr/bin/env python3
"""
g6_regime_robustness.py — Gauntlet G6: Regime-Partitioned Robustness Gate.

Splits a strategy's backtest trades by market regime and verifies the strategy
is profitable across ALL regimes, not just one. A strategy that only works in
bull markets fails G6.

Regime detection:
    - Stocks: rolling linear-regression trend (bull/bear/flat) × volatility
      percentile (high/normal/low) from trade entry prices.
    - Crypto: uses crypto_regime.py components when price data permits, falls
      back to the same price-based classifier.

Output:
    regime_score  (0.0–1.0): fraction of regimes where net R > 0
    passes        (bool):    True when regime_score >= 0.75
    concentration (float):   max fraction of total net R in any single regime
    concentration_exceeded:  True when any regime > 70% of total net R

Usage:
    from g6_regime_robustness import evaluate_g6, classify_regimes

    result = evaluate_g6(trades, asset_class='crypto')
    # result['passes'] → True/False
"""

from __future__ import annotations

import sys
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

# -- Import cost adjuster for G3-adjusted R when available --------------------
sys.path.insert(0, os.path.dirname(__file__))
from cost_adjuster import batch_adjust  # noqa: E402

# -- Try importing crypto_regime for crypto-specific detection ----------------
_compute_volatility_regime = None  # type: ignore[assignment]
_compute_btc_trend = None          # type: ignore[assignment]
try:
    from crypto_regime import _compute_volatility_regime as _crypto_vol_regime
    from crypto_regime import _compute_btc_trend as _crypto_btc_trend
    _compute_volatility_regime = _crypto_vol_regime
    _compute_btc_trend = _crypto_btc_trend
    _HAS_CRYPTO_REGIME = True
except ImportError:
    _HAS_CRYPTO_REGIME = False


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# G6 pass / fail thresholds
REGIME_SCORE_THRESHOLD = 0.75       # must be profitable in ≥75% of regimes
CONCENTRATION_LIMIT = 0.70          # no single regime >70% of total net R
MIN_REGIMES_FOR_MEANINGFUL = 3      # fewer regimes → score is less reliable
MIN_TRADES_PER_REGIME = 3           # regimes with fewer trades are merged/ignored

# Trend classification (linear slope on log prices over window)
BULL_SLOPE_THRESHOLD = 0.005        # >0.5% per-trade drift → bull
BEAR_SLOPE_THRESHOLD = -0.005       # <-0.5% per-trade drift → bear

# Volatility classification (percentile thresholds)
HIGH_VOL_PERCENTILE = 0.80
LOW_VOL_PERCENTILE = 0.20

# Rolling windows (trades, not bars — backtests are sparse)
DEFAULT_TREND_WINDOW = 20           # last 20 trades for trend detection
DEFAULT_VOL_WINDOW = 30             # last 30 trades for vol history


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ensure_numeric(arr) -> np.ndarray:
    a = np.asarray(arr, dtype=float)
    return a[np.isfinite(a)]


def _extract_prices(trades: List[Dict[str, Any]]) -> np.ndarray:
    """Extract trade entry prices as a float array, preserving order."""
    prices = []
    for t in trades:
        try:
            prices.append(float(t.get("entry_price", 0)))
        except (ValueError, TypeError):
            prices.append(float("nan"))
    return np.array(prices, dtype=float)


def _extract_net_r(trades: List[Dict[str, Any]]) -> np.ndarray:
    """Extract net R (gauntlet_r > net_r > r_multiple fallback)."""
    values = []
    for t in trades:
        # Prefer already-adjusted values
        val = t.get("gauntlet_r", None)
        if val is None or val == "" or val == '':
            val = t.get("net_r", None)
        if val is None or val == "" or val == '':
            val = t.get("r_multiple", None)
        try:
            values.append(float(val) if val not in (None, "", '') else 0.0)
        except (ValueError, TypeError):
            values.append(0.0)
    return np.array(values, dtype=float)


def _rolling_slope(prices: np.ndarray, window: int) -> np.ndarray:
    """
    Compute rolling linear regression slope of log prices.
    Returns NaN for indices where window < min required.
    Slope is per-trade (unit: log-price change per trade index step).
    """
    n = len(prices)
    out = np.full(n, np.nan)
    log_p = np.log(np.maximum(prices, 1e-9))

    for i in range(window - 1, n):
        y = log_p[i - window + 1 : i + 1]
        x = np.arange(window, dtype=float)
        # Ordinary least squares slope
        x_mean = x.mean()
        y_mean = y.mean()
        num = np.sum((x - x_mean) * (y - y_mean))
        denom = np.sum((x - x_mean) ** 2)
        if denom > 0:
            out[i] = num / denom
    return out


def _rolling_volatility(prices: np.ndarray, window: int) -> np.ndarray:
    """Compute rolling std of per-trade log returns."""
    n = len(prices)
    out = np.full(n, np.nan)
    log_p = np.log(np.maximum(prices, 1e-9))
    rets = np.diff(log_p)

    for i in range(window, n):
        r = rets[i - window : i]
        if len(r) >= 2:
            out[i] = float(np.std(r, ddof=1))
    return out


# ---------------------------------------------------------------------------
# Regime classification
# ---------------------------------------------------------------------------

def classify_regimes(
    trades: List[Dict[str, Any]],
    asset_class: str = "crypto",
    trend_window: int = DEFAULT_TREND_WINDOW,
    vol_window: int = DEFAULT_VOL_WINDOW,
) -> List[str]:
    """
    Assign a regime label to each trade.

    Returns a list of strings, same length as trades.
    Labels: "{trend}_{vol}" e.g. "bull_normal", "bear_high", "flat_low".

    When data is sparse (< trend_window trades), all trades get "insufficient_data".

    Args:
        trades: list of trade dicts with at least 'entry_price'
        asset_class: 'stock' or 'crypto' (affects which detection is preferred)
        trend_window: number of prior trades for trend slope estimation
        vol_window: number of prior trades for volatility estimation
    """
    if len(trades) < max(trend_window, vol_window):
        return ["insufficient_data"] * len(trades)

    prices = _extract_prices(trades)
    valid_mask = np.isfinite(prices) & (prices > 0)
    if valid_mask.sum() < max(trend_window, vol_window):
        return ["insufficient_data"] * len(trades)

    # Compute rolling metrics
    slopes = _rolling_slope(prices, trend_window)
    vols = _rolling_volatility(prices, vol_window)

    # Volatility percentile: compare each valid vol to historical distribution
    vol_percentiles = np.full(len(vols), np.nan)
    valid_vol_mask = np.isfinite(vols)
    if valid_vol_mask.sum() >= vol_window:
        valid_vols = vols[valid_vol_mask]
        for i in range(len(vols)):
            if valid_vol_mask[i]:
                vol_percentiles[i] = float(
                    np.mean(valid_vols < vols[i])
                )

    # For crypto: if crypto_regime available, blend in vol percentile from it
    if asset_class == "crypto" and _HAS_CRYPTO_REGIME and len(prices) >= 32:
        crypto_vol_fn = _compute_volatility_regime
        if crypto_vol_fn is not None:
            try:
                crypto_vol = crypto_vol_fn(prices)
                crypto_vol_pct = crypto_vol.get("vol_percentile", 0.5)
                # Blend: 50% from trade-level vol, 50% from crypto_regime
                for i in range(len(vol_percentiles)):
                    if not np.isfinite(vol_percentiles[i]):
                        vol_percentiles[i] = crypto_vol_pct
                    else:
                        vol_percentiles[i] = 0.5 * vol_percentiles[i] + 0.5 * crypto_vol_pct
            except Exception:
                pass  # fall back to trade-level vol

    # Classify each trade
    regimes = []
    for i in range(len(trades)):
        if i < trend_window:
            regimes.append("insufficient_data")
            continue

        slope = slopes[i]
        vol_pct = vol_percentiles[i]

        if not np.isfinite(slope):
            regimes.append("insufficient_data")
            continue

        # Trend
        if slope > BULL_SLOPE_THRESHOLD:
            trend = "bull"
        elif slope < BEAR_SLOPE_THRESHOLD:
            trend = "bear"
        else:
            trend = "flat"

        # Volatility
        if not np.isfinite(vol_pct):
            vol_label = "normal"
        elif vol_pct >= HIGH_VOL_PERCENTILE:
            vol_label = "high"
        elif vol_pct <= LOW_VOL_PERCENTILE:
            vol_label = "low"
        else:
            vol_label = "normal"

        regimes.append(f"{trend}_{vol_label}")

    return regimes


def _simplify_regimes(
    regimes: List[str],
    net_r_values: np.ndarray,
    min_trades: int = MIN_TRADES_PER_REGIME,
) -> Tuple[List[str], List[str]]:
    """
    Merge regimes with fewer than min_trades into 'other'.
    Returns (simplified_regimes, unique_regime_names).
    """
    from collections import Counter

    counts = Counter(regimes)
    small_regimes = {r for r, c in counts.items() if c < min_trades and r != "insufficient_data"}

    simplified = []
    for r in regimes:
        if r in small_regimes:
            simplified.append("other")
        else:
            simplified.append(r)

    unique = [r for r in dict.fromkeys(simplified) if r != "insufficient_data"]
    return simplified, unique


# ---------------------------------------------------------------------------
# G6 evaluation
# ---------------------------------------------------------------------------

@dataclass
class RegimeStats:
    """Per-regime statistics."""
    regime: str
    trade_count: int
    total_net_r: float
    avg_net_r: float
    win_rate: float
    profitable: bool  # net R > 0


def evaluate_g6(
    trades: List[Dict[str, Any]],
    asset_class: Optional[str] = None,
    apply_cost_adjustment: bool = True,
) -> Dict[str, Any]:
    """
    G6 gate: regime-partitioned robustness.

    1. Classify each trade into a market regime.
    2. Compute net R (after G3 cost drag) for trades in each regime.
    3. regime_score = fraction of regimes where net R > 0.
    4. Check concentration: no single regime > 70% of total net R.
    5. Pass threshold: regime_score >= 0.75.

    Args:
        trades: list of trade dicts with entry_price, r_multiple (or net_r/gauntlet_r)
        asset_class: 'stock' or 'crypto'. Auto-detected if None (from trade fields).
        apply_cost_adjustment: if True, run batch_adjust to compute gauntlet_r

    Returns:
        dict with keys: regime_score, passes, regime_breakdown, concentration,
                        concentration_exceeded, regime_count, profitable_regimes,
                        total_trades, total_net_r
    """
    if not trades:
        return {
            "regime_score": 0.0,
            "passes": False,
            "regime_breakdown": {},
            "concentration": 0.0,
            "concentration_exceeded": False,
            "regime_count": 0,
            "profitable_regimes": 0,
            "total_trades": 0,
            "total_net_r": 0.0,
            "error": "no trades provided",
        }

    # Auto-detect asset class
    if asset_class is None:
        first_asset = trades[0].get("asset_class", "").lower()
        first_symbol = str(trades[0].get("symbol", "")).upper()
        if first_asset in ("stock", "crypto"):
            asset_class = first_asset
        elif first_symbol in ("SPY", "QQQ", "IWM", "AAPL", "MSFT", "TSLA", "NVDA"):
            asset_class = "stock"
        else:
            asset_class = "crypto"

    # Apply G3 cost adjustment if not already done
    if apply_cost_adjustment:
        # Check if gauntlet_r already present
        has_gauntlet = any(
            t.get("gauntlet_r") not in (None, "", '') for t in trades[:5]
        )
        if not has_gauntlet:
            batch_adjust(trades)

    # Extract net R values
    net_r_values = _extract_net_r(trades)

    # Classify regimes
    regimes = classify_regimes(trades, asset_class)

    # Filter out insufficient_data trades
    valid_indices = [i for i, r in enumerate(regimes) if r != "insufficient_data"]
    if len(valid_indices) < MIN_TRADES_PER_REGIME:
        return {
            "regime_score": 0.0,
            "passes": False,
            "regime_breakdown": {},
            "concentration": 0.0,
            "concentration_exceeded": False,
            "regime_count": 0,
            "profitable_regimes": 0,
            "total_trades": len(trades),
            "total_net_r": float(np.sum(net_r_values)),
            "error": "insufficient classified trades for regime analysis",
        }

    valid_regimes = [regimes[i] for i in valid_indices]
    valid_net_r = net_r_values[valid_indices]

    # Merge tiny regimes
    simplified, unique_regimes = _simplify_regimes(valid_regimes, valid_net_r)

    # Compute per-regime stats
    breakdown: Dict[str, Dict[str, Any]] = {}
    profitable_count = 0

    for regime in unique_regimes:
        mask = np.array([r == regime for r in simplified])
        regime_r = valid_net_r[mask]
        total_r = float(np.sum(regime_r))
        avg_r = total_r / len(regime_r) if len(regime_r) > 0 else 0.0
        wins = float(np.sum(regime_r > 0))
        wr = wins / len(regime_r) if len(regime_r) > 0 else 0.0
        profitable = total_r > 0

        breakdown[regime] = {
            "trade_count": int(len(regime_r)),
            "total_net_r": total_r,
            "avg_net_r": avg_r,
            "win_rate": wr,
            "profitable": profitable,
        }
        if profitable:
            profitable_count += 1

    total_net_r = float(np.sum(valid_net_r))
    regime_count = len(unique_regimes)

    # Regime score
    regime_score = profitable_count / regime_count if regime_count > 0 else 0.0

    # Concentration: max fraction of total net R in any single regime
    concentration = 0.0
    if regime_count > 0 and abs(total_net_r) > 1e-9:
        for regime in unique_regimes:
            r_total = breakdown[regime]["total_net_r"]
            fraction = abs(r_total) / abs(total_net_r) if abs(total_net_r) > 0 else 0.0
            concentration = max(concentration, fraction)

    concentration_exceeded = concentration > CONCENTRATION_LIMIT

    # Final pass/fail: score >= threshold AND no concentration violation
    passes = regime_score >= REGIME_SCORE_THRESHOLD and not concentration_exceeded
    if regime_count < MIN_REGIMES_FOR_MEANINGFUL:
        passes = False  # not enough regime diversity for a meaningful test

    return {
        "regime_score": round(regime_score, 4),
        "passes": passes,
        "regime_breakdown": breakdown,
        "concentration": round(concentration, 4),
        "concentration_exceeded": concentration_exceeded,
        "regime_count": regime_count,
        "profitable_regimes": profitable_count,
        "total_trades": len(trades),
        "total_net_r": round(total_net_r, 4),
        "asset_class": asset_class,
        "threshold": REGIME_SCORE_THRESHOLD,
        "concentration_limit": CONCENTRATION_LIMIT,
    }


# ---------------------------------------------------------------------------
# CLI: standalone evaluation
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import csv
    import json

    trades_path = sys.argv[1] if len(sys.argv) > 1 else None

    if trades_path is None or not os.path.exists(trades_path or ""):
        print("Usage: python g6_regime_robustness.py <backtest_csv>")
        print("ERROR: file not found" if trades_path else "ERROR: no file specified")
        if trades_path is None:
            sys.exit(0)
        sys.exit(1)

    with open(trades_path) as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    result = evaluate_g6(rows)

    print("=" * 60)
    print("GAUNTLET G6: REGIME-PARTITIONED ROBUSTNESS")
    print("=" * 60)
    print(f"Trades:       {result['total_trades']}")
    print(f"Asset class:  {result['asset_class']}")
    print(f"Total net R:  {result['total_net_r']:+.4f}")
    print()
    print(f"Regime score: {result['regime_score']:.2%} (need ≥{result['threshold']:.0%})")
    print(f"Regimes:      {result['regime_count']} ({result['profitable_regimes']} profitable)")
    print(f"Concentration:{result['concentration']:.2%} (limit ≤{result['concentration_limit']:.0%})")
    print(f"Concentration exceeded: {result['concentration_exceeded']}")
    print()
    print(f"PASS: {result['passes']}")
    print()

    if result["regime_breakdown"]:
        print("Regime breakdown:")
        for regime, stats in sorted(result["regime_breakdown"].items()):
            pf = "✓" if stats["profitable"] else "✗"
            print(f"  {pf} {regime:20s}  n={stats['trade_count']:3d}  "
                  f"avg_R={stats['avg_net_r']:+.4f}  "
                  f"total_R={stats['total_net_r']:+.4f}  "
                  f"WR={stats['win_rate']:.1%}")