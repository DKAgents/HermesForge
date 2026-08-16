#!/usr/bin/env python3
"""
scanner_w_flags_pennants.py
==========================
HermesForge STR-W: Flags and Pennants Continuation

Detect a sharp move (mast) of 5+ bars in one direction with >5% gain, then
a consolidation of 5-15 bars:
  - Flag:    parallel channel sloping against the mast trend
  - Pennant: converging trendlines

Entry on breakout from the consolidation in the direction of the original
mast. Stop 1 ATR inside the consolidation. Target = mast height projected
from the breakout. Long-only for stocks.

Dependencies: pandas, numpy, scipy
"""

import sys
import pandas as pd
import numpy as np
from pathlib import Path
from scipy.signal import find_peaks

STRATEGY_ID = "STR-W-flags-pennants"
STRATEGY_NAME = "Flags and Pennants Continuation"
STRATEGY_VERSION = "1.0"
MAX_HOLD_BARS = 25
MAST_MIN_BARS = 5
MAST_MIN_GAIN = 0.05
CONSOL_MIN = 5
CONSOL_MAX = 15
STOP_ATR_MULT = 1.0
PIVOT_DISTANCE = 2
PARALLEL_TOL = 0.25  # slope ratio tolerance for "parallel"


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


def _fit_slope(idx_list, price_list):
    if len(idx_list) < 2:
        return None
    x = np.array(idx_list, dtype=float)
    y = np.array(price_list, dtype=float)
    slope, _ = np.polyfit(x, y, 1)
    return slope


def scan(df: pd.DataFrame, ticker: str, long_only: bool = False) -> list:
    if len(df) < 40:
        return []

    atr = _compute_atr(df)
    n = len(df)
    close = df["close"].values
    high = df["high"].values
    low = df["low"].values
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

    # walk through candidate mast starts
    for mast_start in range(0, n - (MAST_MIN_BARS + CONSOL_MIN + 1)):
        # find the mast end: the bar with the max gain over MAST_MIN_BARS+ bars
        best_end = -1
        best_gain = 0.0
        for me in range(mast_start + MAST_MIN_BARS - 1, min(mast_start + 25, n - CONSOL_MIN - 1)):
            gain = (close[me] - close[mast_start]) / close[mast_start]
            if gain > best_gain:
                best_gain = gain
                best_end = me
        if best_end < 0 or best_gain < MAST_MIN_GAIN:
            continue
        mast_end = best_end
        mast_h = close[mast_end] - close[mast_start]  # bullish mast
        direction = "long"
        if not long_only:
            # also check for down-mast
            best_gain_d = 0.0
            best_end_d = -1
            for me in range(mast_start + MAST_MIN_BARS - 1, min(mast_start + 25, n - CONSOL_MIN - 1)):
                gain = (close[mast_start] - close[me]) / close[mast_start]
                if gain > best_gain_d:
                    best_gain_d = gain
                    best_end_d = me
            if best_gain_d > best_gain and best_gain_d >= MAST_MIN_GAIN:
                mast_end = best_end_d
                mast_h = close[mast_start] - close[mast_end]
                direction = "short"
                best_gain = best_gain_d
        if mast_h <= 0:
            continue

        # consolidation window after mast_end
        consol_end_max = min(mast_end + CONSOL_MAX, n - 1)
        if consol_end_max - mast_end < CONSOL_MIN:
            continue

        # find swing highs/lows within the consolidation
        for ce in range(mast_end + CONSOL_MIN, consol_end_max + 1):
            win_high = high[mast_end + 1:ce + 1]
            win_low = low[mast_end + 1:ce + 1]
            wpos = np.arange(mast_end + 1, ce + 1)
            if len(win_high) < 2:
                continue
            shs, _ = find_peaks(win_high, distance=PIVOT_DISTANCE)
            sls, _ = find_peaks(-win_low, distance=PIVOT_DISTANCE)
            if len(shs) < 2 or len(sls) < 2:
                continue
            up_slope = _fit_slope(wpos[shs], win_high[shs])
            lo_slope = _fit_slope(wpos[sls], win_low[sls])
            if up_slope is None or lo_slope is None:
                continue

            # classify: pennant if slopes converge (opposite signs or
            # |up_slope - lo_slope| large and converging); flag if parallel
            slope_ratio = lo_slope / up_slope if up_slope != 0 else 0.0
            is_pennant = (up_slope * lo_slope < 0) or (abs(up_slope - lo_slope) / (abs(up_slope) + 1e-9) > 0.6)
            is_flag = abs(slope_ratio - 1.0) < PARALLEL_TOL if up_slope != 0 else False
            if not (is_pennant or is_flag):
                continue

            # upper/lower line value at ce
            x = ce
            upper = win_high[shs[-1]] + up_slope * (x - wpos[shs][-1])
            lower = win_low[sls[-1]] + lo_slope * (x - wpos[sls][-1])
            # must still be contracting / contained
            if upper <= lower:
                continue

            brk_idx = ce + 1
            if brk_idx >= n:
                continue
            c = close[brk_idx]

            if direction == "long":
                if c > upper:
                    entry = c
                    stop = lower - STOP_ATR_MULT * atr.iloc[brk_idx]
                    risk = entry - stop
                    if risk <= 0:
                        continue
                    target = entry + mast_h
                    st = "pennant_long" if is_pennant else "flag_long"
                    make(brk_idx, "long", entry, stop, target, st)
            else:
                if c < lower:
                    entry = c
                    stop = upper + STOP_ATR_MULT * atr.iloc[brk_idx]
                    risk = stop - entry
                    if risk <= 0:
                        continue
                    target = entry - mast_h
                    st = "pennant_short" if is_pennant else "flag_short"
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
    print(f"STR-W Flags/Pennants Phase 1A ({asset_type})")
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
    ap = argparse.ArgumentParser(description="STR-W Flags/Pennants Scanner")
    ap.add_argument("--backtest", action="store_true")
    ap.add_argument("--crypto", action="store_true")
    args = ap.parse_args()
    if args.backtest:
        if args.crypto:
            symbols = ["BTC", "ETH", "SOL", "OP", "ARB", "AVAX", "DOGE", "LINK"]
            print("=== STR-W Phase 1A Backtest (Crypto) ===\n")
            result = run_phase1a(symbols, "crypto")
        else:
            symbols = ["SPY", "QQQ", "AAPL", "NVDA", "TSLA", "AMZN", "MSFT", "GOOGL",
                       "META", "AMD", "NFLX", "JPM", "BAC", "XOM", "CVX", "PFE", "UNH", "COST"]
            print("=== STR-W Phase 1A Backtest (Stocks) ===\n")
            result = run_phase1a(symbols, "stock")
            if len(result) > 0:
                out_path = Path(__file__).parent.parent / "results" / "STR-W-stocks-phase1a.csv"
                out_path.parent.mkdir(parents=True, exist_ok=True)
                result.to_csv(out_path, index=False)
                print(f"\nResults saved to {out_path}")
    else:
        print(__doc__)
