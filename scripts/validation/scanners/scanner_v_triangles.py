#!/usr/bin/env python3
"""
scanner_v_triangles.py
=====================
HermesForge STR-V: Triangle Breakout

Detect a contracting range over 20+ bars and classify the triangle:
  - Symmetrical:  lower highs + higher lows  (both lines converge)
  - Ascending:    flat highs + rising lows
  - Descending:   falling highs + flat lows

Entry on the breakout bar that closes outside the triangle with volume
> 1.5x the rolling average. Stop at the opposite side of the triangle at
the breakout bar. Target = triangle base height (max range within the
formation) projected from the breakout point.

Dependencies: pandas, numpy, scipy
"""

import sys
import pandas as pd
import numpy as np
from pathlib import Path
from scipy.signal import find_peaks

STRATEGY_ID = "STR-V-triangles"
STRATEGY_NAME = "Triangle Breakout"
STRATEGY_VERSION = "1.0"
MAX_HOLD_BARS = 25
MIN_WINDOW = 20
VOLUME_MULT = 1.5
PIVOT_DISTANCE = 3
FLAT_TOL = 0.001  # slope tolerance for "flat" lines (fraction of price)


def _compute_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    high = df["high"]
    low = df["low"]
    close = df["close"]
    prev_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs(),
    ], axis=1).max(axis=1)
    return tr.ewm(alpha=1 / period, adjust=False).mean()


def _find_pivots(df: pd.DataFrame, distance: int = PIVOT_DISTANCE):
    high = df["high"].values
    low = df["low"].values
    sh_idx, _ = find_peaks(high, distance=distance)
    sl_idx, _ = find_peaks(-low, distance=distance)
    return list(sh_idx), list(sl_idx)


def _fit_line(idx_list, price_list, x_end):
    """Linear regression through (idx, price) points; return (slope, intercept_at_x_end)."""
    if len(idx_list) < 2:
        return None, None
    x = np.array(idx_list, dtype=float)
    y = np.array(price_list, dtype=float)
    slope, intercept = np.polyfit(x, y, 1)
    return slope, intercept + slope * x_end


def scan(df: pd.DataFrame, ticker: str, long_only: bool = False) -> list:
    if len(df) < MIN_WINDOW + 10:
        return []

    atr = _compute_atr(df)
    sh_idx, sl_idx = _find_pivots(df)
    n = len(df)
    close = df["close"].values
    high = df["high"].values
    low = df["low"].values
    has_vol = "volume" in df.columns
    vol = df["volume"].values if has_vol else np.ones(n)
    avg_vol = pd.Series(vol).rolling(20).mean().values
    signals = []

    def make(idx, direction, entry, stop, target, st):
        signals.append({
            "date": df.index[idx],
            "ticker": ticker,
            "strategy_id": STRATEGY_ID,
            "strategy_name": STRATEGY_NAME,
            "strategy_version": STRATEGY_VERSION,
            "direction": direction,
            "entry_price": round(entry, 6),
            "stop_price": round(stop, 6),
            "target_price": round(target, 6),
            "atr": float(atr.iloc[idx]),
            "signal_type": st,
        })

    # Slide a window; for each end bar, look back MIN_WINDOW bars and try to
    # fit upper/lower trendlines from swing pivots within that window.
    for end in range(MIN_WINDOW, n - 1):
        start = end - MIN_WINDOW
        # Only use pivots confirmed by end+1: a pivot at bar j is confirmed
        # only if end - j >= PIVOT_DISTANCE (find_peaks(distance=N) requires
        # N future bars to confirm a peak).
        shs = [j for j in sh_idx if start <= j <= end - PIVOT_DISTANCE]
        sls = [j for j in sl_idx if start <= j <= end - PIVOT_DISTANCE]
        if len(shs) < 2 or len(sls) < 2:
            continue
        # fit lines evaluated at end bar
        up_slope, up_int = _fit_line(shs, [high[j] for j in shs], end)
        lo_slope, lo_int = _fit_line(sls, [low[j] for j in sls], end)
        if up_slope is None or lo_slope is None:
            continue
        upper_at_end = up_int
        lower_at_end = lo_int
        if upper_at_end <= lower_at_end:
            continue  # not contracting / invalid

        base_height = np.max(high[start:end + 1]) - np.min(low[start:end + 1])
        if base_height <= 0:
            continue

        mid = (upper_at_end + lower_at_end) / 2.0
        # classify
        flat_band = abs(mid) * FLAT_TOL
        up_flat = abs(up_slope) < flat_band / 10  # slope per bar
        lo_flat = abs(lo_slope) < flat_band / 10

        brk_idx = end + 1
        if brk_idx >= n:
            continue
        v = vol[brk_idx]
        av = avg_vol[brk_idx] if not np.isnan(avg_vol[brk_idx]) else v
        vol_ok = (v >= VOLUME_MULT * av) if (has_vol and av > 0) else True

        c = close[brk_idx]

        # breakout ABOVE upper line → long
        if c > upper_at_end and vol_ok:
            entry = c
            stop = lower_at_end
            risk = entry - stop
            if risk <= 0:
                continue
            target = entry + base_height
            st = "triangle_breakout_long"
            if up_flat and not lo_flat:
                st = "ascending_triangle_long"
            elif lo_flat and not up_flat:
                st = "descending_long"
            elif up_slope < 0 < lo_slope:
                st = "symmetrical_triangle_long"
            make(brk_idx, "long", entry, stop, target, st)

        # breakout BELOW lower line → short
        if (not long_only) and c < lower_at_end and vol_ok:
            entry = c
            stop = upper_at_end
            risk = stop - entry
            if risk <= 0:
                continue
            target = entry - base_height
            st = "triangle_breakout_short"
            if lo_flat and not up_flat:
                st = "descending_triangle_short"
            elif up_flat and not lo_flat:
                st = "ascending_short"
            elif up_slope < 0 < lo_slope:
                st = "symmetrical_triangle_short"
            make(brk_idx, "short", entry, stop, target, st)

    return signals


def _walk_forward_exit(df: pd.DataFrame, entry_idx: int, direction: str,
                       entry_price: float, stop_price: float,
                       target_price: float, max_bars: int = MAX_HOLD_BARS) -> dict:
    n = len(df)
    for i in range(entry_idx + 1, min(entry_idx + max_bars + 1, n)):
        bar = df.iloc[i]
        if direction == "long":
            if bar["low"] <= stop_price:
                return {"exit_type": "stop", "exit_price": stop_price,
                        "bars_held": i - entry_idx, "r_multiple": -1.0}
            if bar["high"] >= target_price:
                return {"exit_type": "target", "exit_price": target_price,
                        "bars_held": i - entry_idx, "r_multiple": None}
        else:
            if bar["high"] >= stop_price:
                return {"exit_type": "stop", "exit_price": stop_price,
                        "bars_held": i - entry_idx, "r_multiple": -1.0}
            if bar["low"] <= target_price:
                return {"exit_type": "target", "exit_price": target_price,
                        "bars_held": i - entry_idx, "r_multiple": None}
    exit_bar = df.iloc[min(entry_idx + max_bars, n - 1)]
    exit_price = exit_bar["close"]
    risk = entry_price - stop_price if direction == "long" else stop_price - entry_price
    r = (exit_price - entry_price) / risk if direction == "long" else (entry_price - exit_price) / risk
    if risk <= 0:
        r = 0.0
    return {"exit_type": "time", "exit_price": exit_price,
            "bars_held": max_bars, "r_multiple": round(r, 3)}


def run_backtest(df: pd.DataFrame, ticker: str, long_only: bool = False) -> list:
    signals = scan(df, ticker, long_only=long_only)
    if not signals:
        return []
    trades = []
    n = len(df)
    for sig in signals:
        try:
            target_date = pd.Timestamp(sig["date"])
            mask = df.index == target_date
            if not mask.any():
                continue
            entry_idx = df.index.get_loc(df.index[mask][0])
        except (ValueError, KeyError, TypeError):
            continue
        if entry_idx + 1 >= n:
            continue
        exit_result = _walk_forward_exit(
            df, entry_idx, sig["direction"],
            sig["entry_price"], sig["stop_price"], sig["target_price"])
        r_mult = exit_result["r_multiple"]
        if r_mult is None:
            risk = (sig["entry_price"] - sig["stop_price"]) if sig["direction"] == "long" \
                else (sig["stop_price"] - sig["entry_price"])
            gain = (exit_result["exit_price"] - sig["entry_price"]) if sig["direction"] == "long" \
                else (sig["entry_price"] - exit_result["exit_price"])
            r_mult = round(gain / risk, 3) if risk > 0 else 0.0
        trades.append({
            "symbol": ticker, "strategy": STRATEGY_ID,
            "direction": sig["direction"], "date": sig["date"],
            "entry_price": round(sig["entry_price"], 4),
            "stop_price": round(sig["stop_price"], 4),
            "target_price": round(sig["target_price"], 4),
            "exit_type": exit_result["exit_type"],
            "exit_price": round(exit_result["exit_price"], 4),
            "bars_held": exit_result["bars_held"],
            "r_multiple": r_mult,
            "signal_type": sig["signal_type"],
        })
    return trades


def run_phase1a(symbols: list, asset_type: str = "stock") -> pd.DataFrame:
    DATA_DIR = Path.home() / ".hermes" / "market_data"
    all_trades = []
    for sym in symbols:
        print(f"  Scanning {sym}...", flush=True)
        cache_path = DATA_DIR / f"{sym}.parquet"
        if not cache_path.exists():
            print(f"    No cached data for {sym}")
            continue
        df = pd.read_parquet(cache_path)
        if "Date" in df.columns:
            df = df.set_index("Date")
        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index)
        if len(df) < 60:
            print(f"    Only {len(df)} bars — skipping")
            continue
        long_only = (asset_type == "stock")
        trades = run_backtest(df, sym, long_only=long_only)
        all_trades.extend(trades)
        print(f"    {len(trades)} signals found")

    if not all_trades:
        print("\nNo signals found across all symbols!")
        return pd.DataFrame()

    df = pd.DataFrame(all_trades)
    print(f"\n{'='*60}")
    print(f"STR-V Triangles Phase 1A ({asset_type})")
    print(f"{'='*60}")
    print(f"Total signals: {len(df)}")
    print(f"Win rate: {(df['r_multiple'] > 0).mean() * 100:.1f}%")
    print(f"Average R: {df['r_multiple'].mean():.3f}")
    print(f"Median R: {df['r_multiple'].median():.3f}")
    print(f"Sum R: {df['r_multiple'].sum():.3f}")
    print(f"Max win: {df['r_multiple'].max():.3f}R")
    print(f"Max loss: {df['r_multiple'].min():.3f}R")
    print(f"Avg bars held: {df['bars_held'].mean():.1f}")

    print(f"\nBy direction:")
    for d in ["long", "short"]:
        s = df[df["direction"] == d]
        if len(s) > 0:
            print(f"  {d}: {len(s)} trades, WR={((s['r_multiple'] > 0).mean() * 100):.1f}%, "
                  f"avg R={s['r_multiple'].mean():.3f}")

    print(f"\nBy signal type:")
    for st in sorted(df["signal_type"].unique()):
        s = df[df["signal_type"] == st]
        if len(s) > 0:
            print(f"  {st}: {len(s)} trades, WR={((s['r_multiple'] > 0).mean() * 100):.1f}%, "
                  f"avg R={s['r_multiple'].mean():.3f}")

    print(f"\nBy exit type:")
    for et in ["target", "stop", "time"]:
        s = df[df["exit_type"] == et]
        if len(s) > 0:
            print(f"  {et}: {len(s)} trades, avg R={s['r_multiple'].mean():.3f}")

    pos_r = df[df["r_multiple"] > 0]["r_multiple"].sum()
    neg_r = abs(df[df["r_multiple"] < 0]["r_multiple"].sum())
    pf = pos_r / neg_r if neg_r > 0 else float('inf')
    print(f"\nProfit factor: {pf:.2f}")
    return df


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="STR-V Triangles Scanner")
    ap.add_argument("--backtest", action="store_true")
    ap.add_argument("--crypto", action="store_true")
    args = ap.parse_args()
    if args.backtest:
        if args.crypto:
            symbols = ["BTC", "ETH", "SOL", "OP", "ARB", "AVAX", "DOGE", "LINK"]
            print("=== STR-V Phase 1A Backtest (Crypto) ===\n")
            result = run_phase1a(symbols, "crypto")
        else:
            symbols = ["SPY", "QQQ", "AAPL", "NVDA", "TSLA", "AMZN", "MSFT", "GOOGL",
                       "META", "AMD", "NFLX", "JPM", "BAC", "XOM", "CVX", "PFE", "UNH", "COST"]
            print("=== STR-V Phase 1A Backtest (Stocks) ===\n")
            result = run_phase1a(symbols, "stock")
            if len(result) > 0:
                out_path = Path(__file__).parent.parent / "results" / "STR-V-stocks-phase1a.csv"
                out_path.parent.mkdir(parents=True, exist_ok=True)
                result.to_csv(out_path, index=False)
                print(f"\nResults saved to {out_path}")
    else:
        print(__doc__)
