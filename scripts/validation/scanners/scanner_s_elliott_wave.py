#!/usr/bin/env python3
"""
scanner_s_elliott_wave.py
========================
HermesForge STR-S: Elliott Wave Corrective Completion

Detect a 5-wave impulse (5 consecutive higher highs/lows for bullish, or
lower highs/lows for bearish), then an A-B-C correction where wave C
retraces 38.2%-61.8% of the impulse. Entry triggers when the correction
completes — i.e. price closes back in the impulse direction past the
wave B high (long) / low (short).

Risk management:
  Stop:   1 ATR below the correction low (long) / above correction high (short)
  Target: 3R
  Time stop: 25 bars

Dependencies: pandas, numpy, scipy
"""

import sys
import pandas as pd
import numpy as np
from pathlib import Path
from scipy.signal import find_peaks

STRATEGY_ID = "STR-S-elliott-wave"
STRATEGY_NAME = "Elliott Wave Corrective Completion"
STRATEGY_VERSION = "1.0"
MAX_HOLD_BARS = 25
TARGET_RR = 3.0
STOP_ATR_MULT = 1.0
FIB_MIN = 0.382
FIB_MAX = 0.618
PIVOT_DISTANCE = 3   # min bars between pivots
ENTRY_SEARCH_WINDOW = 15  # bars after pivot confirmation to search for entry


def _compute_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Compute Average True Range."""
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
    """Return (swing_high_idx, swing_low_idx) as lists of integer positions."""
    high = df["high"].values
    low = df["low"].values
    sh_idx, _ = find_peaks(high, distance=distance)
    sl_idx, _ = find_peaks(-low, distance=distance)
    return list(sh_idx), list(sl_idx)


def scan(df: pd.DataFrame, ticker: str, long_only: bool = False) -> list:
    """Scan for Elliott Wave corrective-completion signals."""
    if len(df) < 60:
        return []

    atr = _compute_atr(df)
    sh_idx, sl_idx = _find_pivots(df)

    signals = []
    n = len(df)

    def make_signal(idx, direction, entry, stop, target, extra):
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
            "signal_type": extra.get("signal_type", "elliott_wave"),
        })

    # ── BULLISH: 5-wave impulse up ──
    # Need 5 swing highs each higher than the previous; the impulse starts at
    # the swing low immediately before the first of those 5 swing highs.
    for i in range(4, len(sh_idx)):
        five = sh_idx[i - 4: i + 1]
        highs = [df["high"].values[j] for j in five]
        if all(highs[k] > highs[k - 1] for k in range(1, 5)):
            # impulse start = nearest swing low before five[0]
            start_lows = [j for j in sl_idx if j < five[0]]
            if not start_lows:
                continue
            start_low_idx = start_lows[-1]
            start_low = df["low"].values[start_low_idx]
            peak5 = highs[-1]
            peak5_idx = five[-1]
            impulse_h = peak5 - start_low

            # Need A-B-C correction after peak5
            # A = first swing low after peak5
            a_lows = [j for j in sl_idx if j > peak5_idx]
            if not a_lows:
                continue
            a_idx = a_lows[0]
            a_price = df["low"].values[a_idx]
            # B = first swing high after A
            b_highs = [j for j in sh_idx if j > a_idx]
            if not b_highs:
                continue
            b_idx = b_highs[0]
            b_price = df["high"].values[b_idx]
            if b_price >= peak5:
                continue  # B must be lower than the impulse peak
            # C = first swing low after B
            c_lows = [j for j in sl_idx if j > b_idx]
            if not c_lows:
                continue
            c_idx = c_lows[0]
            c_price = df["low"].values[c_idx]

            # C retraces 38.2%-61.8% of the impulse (measured from peak down)
            retr = peak5 - c_price
            if impulse_h <= 0:
                continue
            retr_pct = retr / impulse_h
            if not (FIB_MIN <= retr_pct <= FIB_MAX):
                continue

            # Entry: price closes back above wave B high (impulse resumption)
            # NOTE: start search at c_idx + PIVOT_DISTANCE so the C pivot is
            # confirmed by find_peaks(distance=PIVOT_DISTANCE) before entry.
            for j in range(c_idx + PIVOT_DISTANCE, min(c_idx + ENTRY_SEARCH_WINDOW, n)):
                if df["close"].values[j] > b_price:
                    entry = df["close"].values[j]
                    stop = c_price - STOP_ATR_MULT * atr.iloc[j]
                    risk = entry - stop
                    if risk <= 0:
                        break
                    target = entry + risk * TARGET_RR
                    make_signal(j, "long", entry, stop, target,
                                {"signal_type": "elliott_abc_long",
                                 "retracement_pct": retr_pct})
                    break  # one signal per impulse

    # ── BEARISH: 5-wave impulse down ──
    if not long_only:
        for i in range(4, len(sl_idx)):
            five = sl_idx[i - 4: i + 1]
            lows = [df["low"].values[j] for j in five]
            if all(lows[k] < lows[k - 1] for k in range(1, 5)):
                start_highs = [j for j in sh_idx if j < five[0]]
                if not start_highs:
                    continue
                start_high_idx = start_highs[-1]
                start_high = df["high"].values[start_high_idx]
                trough5 = lows[-1]
                trough5_idx = five[-1]
                impulse_h = start_high - trough5

                a_highs = [j for j in sh_idx if j > trough5_idx]
                if not a_highs:
                    continue
                a_idx = a_highs[0]
                a_price = df["high"].values[a_idx]
                b_lows = [j for j in sl_idx if j > a_idx]
                if not b_lows:
                    continue
                b_idx = b_lows[0]
                b_price = df["low"].values[b_idx]
                if b_price <= trough5:
                    continue
                c_highs = [j for j in sh_idx if j > b_idx]
                if not c_highs:
                    continue
                c_idx = c_highs[0]
                c_price = df["high"].values[c_idx]

                retr = c_price - trough5
                if impulse_h <= 0:
                    continue
                retr_pct = retr / impulse_h
                if not (FIB_MIN <= retr_pct <= FIB_MAX):
                    continue

                # NOTE: start search at c_idx + PIVOT_DISTANCE so the C pivot is
                # confirmed by find_peaks(distance=PIVOT_DISTANCE) before entry.
                for j in range(c_idx + PIVOT_DISTANCE, min(c_idx + ENTRY_SEARCH_WINDOW, n)):
                    if df["close"].values[j] < b_price:
                        entry = df["close"].values[j]
                        stop = c_price + STOP_ATR_MULT * atr.iloc[j]
                        risk = stop - entry
                        if risk <= 0:
                            break
                        target = entry - risk * TARGET_RR
                        make_signal(j, "short", entry, stop, target,
                                    {"signal_type": "elliott_abc_short",
                                     "retracement_pct": retr_pct})
                        break

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
                        "bars_held": i - entry_idx, "r_multiple": TARGET_RR}
        else:
            if bar["high"] >= stop_price:
                return {"exit_type": "stop", "exit_price": stop_price,
                        "bars_held": i - entry_idx, "r_multiple": -1.0}
            if bar["low"] <= target_price:
                return {"exit_type": "target", "exit_price": target_price,
                        "bars_held": i - entry_idx, "r_multiple": TARGET_RR}

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
        trades.append({
            "symbol": ticker,
            "strategy": STRATEGY_ID,
            "direction": sig["direction"],
            "date": sig["date"],
            "entry_price": round(sig["entry_price"], 4),
            "stop_price": round(sig["stop_price"], 4),
            "target_price": round(sig["target_price"], 4),
            "exit_type": exit_result["exit_type"],
            "exit_price": round(exit_result["exit_price"], 4),
            "bars_held": exit_result["bars_held"],
            "r_multiple": exit_result["r_multiple"],
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
    print(f"STR-S Elliott Wave Corrective Completion Phase 1A ({asset_type})")
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
    ap = argparse.ArgumentParser(description="STR-S Elliott Wave Scanner")
    ap.add_argument("--backtest", action="store_true")
    ap.add_argument("--crypto", action="store_true")
    args = ap.parse_args()

    if args.backtest:
        if args.crypto:
            symbols = ["BTC", "ETH", "SOL", "OP", "ARB", "AVAX", "DOGE", "LINK"]
            print("=== STR-S Phase 1A Backtest (Crypto) ===\n")
            result = run_phase1a(symbols, "crypto")
        else:
            symbols = ["SPY", "QQQ", "AAPL", "NVDA", "TSLA", "AMZN", "MSFT", "GOOGL",
                       "META", "AMD", "NFLX", "JPM", "BAC", "XOM", "CVX", "PFE", "UNH", "COST"]
            print("=== STR-S Phase 1A Backtest (Stocks) ===\n")
            result = run_phase1a(symbols, "stock")
            if len(result) > 0:
                out_path = Path(__file__).parent.parent / "results" / "STR-S-stocks-phase1a.csv"
                out_path.parent.mkdir(parents=True, exist_ok=True)
                result.to_csv(out_path, index=False)
                print(f"\nResults saved to {out_path}")
    else:
        print(__doc__)
