"""
G0 Cost Pre-Screen for Strategy Gauntlet (PROP-001).

Determines whether a market has sufficient move size to cover round-trip costs.
A strategy CANNOT be profitable if median bar moves are smaller than 4x all-in cost.

Cost model:
    all_in_cost_bps = taker_fees(9 bps) + estimated_slippage + funding_overhead
    gross_capture_needed_bps = all_in_cost_bps * 4
    passes = median_abs_move_bps >= gross_capture_needed_bps
"""
from __future__ import annotations

import os
import glob
from typing import Dict, List, Optional, Union

import numpy as np
import pandas as pd

# Default cost parameters (Hyperliquid base perp tier)
TAKER_FEE_BPS = 9.0  # round-trip taker (0.045% * 2)
DEFAULT_SLIPPAGE_BPS = 2.5  # default taker slippage at small size
FUNDING_OVERHEAD_BPS = 2.0  # estimated funding rate overhead
GROSS_MULTIPLIER = 4.0  # gross capture needed = cost * multiplier


def _load_parquet(path: str) -> pd.DataFrame:
    """Load a parquet file and standardize column names."""
    df = pd.read_parquet(path)

    # Standardize column names
    col_map = {}
    for col in df.columns:
        col_lower = col.lower()
        if col_lower in ("timestamp", "date"):
            if "timestamp" in col_lower:
                col_map[col] = "timestamp"
            elif "date" in col_lower:
                col_map[col] = "timestamp"
        elif col_lower in ("open",):
            col_map[col] = "open"
        elif col_lower in ("high",):
            col_map[col] = "high"
        elif col_lower in ("low",):
            col_map[col] = "low"
        elif col_lower in ("close",):
            col_map[col] = "close"
        elif col_lower in ("volume",):
            col_map[col] = "volume"
        elif col_lower in ("trades",):
            col_map[col] = "trades"
        elif col_lower in ("ticker", "symbol"):
            col_map[col] = "symbol"
        elif col_lower in ("subperiod",):
            col_map[col] = "subperiod"
        elif col_lower in ("interval",):
            col_map[col] = "interval"

    if col_map:
        df = df.rename(columns=col_map)

    # Ensure close column exists
    if "close" not in df.columns:
        raise ValueError(f"Parquet file {path} has no recognizable close column. Found: {df.columns.tolist()}")

    return df


def compute_median_abs_move(df: pd.DataFrame, close_col: str = "close") -> float:
    """
    Compute median absolute bar-to-bar percentage move in bps.

    median(|close[i] - close[i-1]| / close[i-1]) * 10000
    """
    closes = df[close_col].dropna().values
    if len(closes) < 2:
        return 0.0

    moves = np.abs(np.diff(closes)) / closes[:-1] * 10000
    return float(np.median(moves))


def screen(
    symbol: str,
    close_prices: Union[List[float], np.ndarray],
    size_usd: Optional[float] = None,
    slippage_bps: Optional[float] = None,
    funding_bps: Optional[float] = None,
    gross_multiplier: Optional[float] = None,
) -> Dict:
    """
    Run G0 cost screen for a symbol given raw close prices.

    Args:
        symbol: ticker identifier
        close_prices: array of close prices
        size_usd: intended order size (unused in batch mode, kept for API compat)
        slippage_bps: override estimated slippage (default: DEFAULT_SLIPPAGE_BPS)
        funding_bps: override funding overhead (default: FUNDING_OVERHEAD_BPS)
        gross_multiplier: override multiplier (default: GROSS_MULTIPLIER)

    Returns:
        Dict with screen results including passes/fail and explanation.
    """
    slippage = slippage_bps if slippage_bps is not None else DEFAULT_SLIPPAGE_BPS
    funding = funding_bps if funding_bps is not None else FUNDING_OVERHEAD_BPS
    multiplier = gross_multiplier if gross_multiplier is not None else GROSS_MULTIPLIER

    arr = np.asarray(close_prices, dtype=float)
    arr = arr[~np.isnan(arr)]

    if len(arr) < 2:
        return {
            "symbol": symbol,
            "median_abs_move_bps": 0.0,
            "all_in_cost_bps": TAKER_FEE_BPS + slippage + funding,
            "gross_capture_needed_bps": (TAKER_FEE_BPS + slippage + funding) * multiplier,
            "passes": False,
            "explanation": f"{symbol}: insufficient data ({len(arr)} bars) for G0 screen",
            "fee_bps": TAKER_FEE_BPS,
            "slippage_bps": slippage,
            "funding_bps": funding,
            "multiplier": multiplier,
        }

    moves = np.abs(np.diff(arr)) / arr[:-1] * 10000
    median_move = float(np.median(moves))

    all_in = TAKER_FEE_BPS + slippage + funding
    gross_needed = all_in * multiplier
    passes = median_move >= gross_needed

    if passes:
        explanation = (
            f"{symbol}: median move {median_move:.1f} bps >= "
            f"gross capture needed {gross_needed:.1f} bps "
            f"(all-in cost {all_in:.1f} bps × {multiplier:.0f}x)"
        )
    else:
        explanation = (
            f"{symbol}: median move {median_move:.1f} bps < "
            f"gross capture needed {gross_needed:.1f} bps — "
            f"all-in cost {all_in:.1f} bps (fees {TAKER_FEE_BPS:.1f} + "
            f"slippage {slippage:.1f} + funding {funding:.1f}) "
            f"× {multiplier:.0f}x requires {gross_needed:.1f} bps capture"
        )

    return {
        "symbol": symbol,
        "median_abs_move_bps": median_move,
        "all_in_cost_bps": all_in,
        "gross_capture_needed_bps": gross_needed,
        "passes": passes,
        "explanation": explanation,
        "fee_bps": TAKER_FEE_BPS,
        "slippage_bps": slippage,
        "funding_bps": funding,
        "multiplier": multiplier,
    }


def screen_from_parquet(
    parquet_path: str,
    timeframe_minutes: Optional[int] = None,
    entry_mode: str = "taker",
    slippage_bps: Optional[float] = None,
    funding_bps: Optional[float] = None,
) -> Dict:
    """
    Load a parquet OHLCV file and run G0 screen.

    Args:
        parquet_path: path to .parquet file
        timeframe_minutes: bar interval (auto-detected if None)
        entry_mode: 'taker' or 'maker' (affects fee model — currently taker only)
        slippage_bps: override slippage
        funding_bps: override funding

    Returns:
        Screen result dict including passes/fail.
    """
    df = _load_parquet(parquet_path)

    # Determine symbol name from filename
    symbol = os.path.splitext(os.path.basename(parquet_path))[0]
    # If symbol has a known column, use it
    if "symbol" in df.columns and not df.empty:
        symbol = str(df["symbol"].iloc[0])

    close_prices = df["close"].dropna().values
    return screen(symbol, close_prices, slippage_bps=slippage_bps, funding_bps=funding_bps)


def batch_screen(
    parquet_dir: str,
    timeframe_minutes: Optional[int] = None,
    pattern: str = "*.parquet",
    slippage_bps: Optional[float] = None,
    funding_bps: Optional[float] = None,
    min_bars: int = 20,
) -> List[Dict]:
    """
    Run G0 screen on all parquet files in a directory.

    Args:
        parquet_dir: directory containing .parquet files
        timeframe_minutes: bar interval
        pattern: glob pattern for files (default: "*.parquet")
        slippage_bps: override slippage
        funding_bps: override funding
        min_bars: skip files with fewer than this many bars

    Returns:
        List of result dicts sorted by median_abs_move_bps descending.
    """
    results = []

    search_pattern = os.path.join(parquet_dir, pattern)
    files = sorted(glob.glob(search_pattern))

    for fpath in files:
        try:
            df = _load_parquet(fpath)
            if len(df) < min_bars:
                continue

            # Determine symbol
            fname = os.path.splitext(os.path.basename(fpath))[0]
            symbol = fname
            if "symbol" in df.columns and not df.empty:
                symbol = str(df["symbol"].iloc[0])

            close_prices = df["close"].dropna().values
            result = screen(
                symbol,
                close_prices,
                slippage_bps=slippage_bps,
                funding_bps=funding_bps,
            )
            result["file"] = fpath
            result["n_bars"] = len(df)
            results.append(result)
        except Exception as e:
            results.append({
                "symbol": os.path.basename(fpath),
                "passes": False,
                "error": str(e),
                "file": fpath,
            })

    results.sort(key=lambda r: r.get("median_abs_move_bps", 0), reverse=True)
    return results


def summary_report(results: List[Dict]) -> Dict:
    """
    Generate a summary report from batch_screen results.

    Returns dict with counts, pass_rate, and per-symbol breakdown.
    """
    valid = [r for r in results if "error" not in r]
    passing = [r for r in valid if r.get("passes", False)]
    failing = [r for r in valid if not r.get("passes", False)]
    errors = [r for r in results if "error" in r]

    return {
        "total_files": len(results),
        "valid": len(valid),
        "pass": len(passing),
        "fail": len(failing),
        "errors": len(errors),
        "pass_rate": len(passing) / len(valid) if valid else 0.0,
        "passing_symbols": [r["symbol"] for r in passing],
        "failing_symbols": [r["symbol"] for r in failing],
        "error_symbols": [r["symbol"] for r in errors],
    }