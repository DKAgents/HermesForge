#!/usr/bin/env python3
"""
scanner_u_double_top_bottom.py
==============================
HermesForge STR-U: Double Top / Double Bottom Reversal

Detect two peaks (double top) or two troughs (double bottom) within 3% of
each other with at least 10 bars between them. Confirmation requires a
close below the trough between the peaks (double top) or above the peak
between the troughs (double bottom).

Risk management:
  Stop:   1 ATR beyond the higher peak (DT) / lower trough (DB)
  Target: pattern height projected from the breakdown/breakup point
  Time stop: 25 bars

Dependencies: pandas, numpy, scipy
"""

import sys
import pandas as pd
import numpy as np
from pathlib import Path
from scipy.signal import find_peaks

STRATEGY_ID = "STR-U-double-top-bottom"
STRATEGY_NAME = "Double Top / Bottom Reversal"
STRATEGY_VERSION = "1.0"
MAX_HOLD_BARS = 25
STOP_ATR_MULT = 1.0
PEAK_TOLERANCE = 0.03
MIN_BARS_BETWEEN = 10
PIVOT_DISTANCE = 4
ENTRY_SEARCH_WINDOW = 15  # bars after pivot confirmation to search for entry


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


def scan(df: pd.DataFrame, ticker: str, long_only: bool = False) -> list:
    if len(df) < 60:
        return []

    atr = _compute_atr(df)
    sh_idx, sl_idx = _find_pivots(df)
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

    # ── Double Top (bearish) ──
    # two swing highs within 3%, >=10 bars apart; trough between them.
    for i in range(1, len(sh_idx)):
        p1_idx = sh_idx[i - 1]
        p2_idx = sh_idx[i]
        if p2_idx - p1_idx < MIN_BARS_BETWEEN:
            continue
        p1, p2 = high[p1_idx], high[p2_idx]
        if abs(p1 - p2) / max(p1, p2) > PEAK_TOLERANCE:
            continue
        troughs = [j for j in sl_idx if p1_idx < j < p2_idx]
        if not troughs:
            continue
        trough_idx = troughs[int(np.argmin([low[j] for j in troughs]))]
        trough_p = low[trough_idx]
        pattern_h = max(p1, p2) - trough_p
        if pattern_h <= 0:
            continue
        # confirmation: first close after p2_idx below trough
        # NOTE: start search at p2_idx + PIVOT_DISTANCE so the second peak
        # is confirmed by find_peaks(distance=PIVOT_DISTANCE) before entry.
        for j in range(p2_idx + PIVOT_DISTANCE, min(p2_idx + ENTRY_SEARCH_WINDOW, n)):
            if close[j] < trough_p:
                entry = close[j]
                stop = max(p1, p2) + STOP_ATR_MULT * atr.iloc[j]
                risk = stop - entry
                if risk <= 0:
                    break
                target = entry - pattern_h
                if (entry - target) < risk:
                    target = entry - risk
                if not long_only:
                    make(j, "short", entry, stop, target, "double_top_short")
                break

    # ── Double Bottom (bullish) ──
    for i in range(1, len(sl_idx)):
        t1_idx = sl_idx[i - 1]
        t2_idx = sl_idx[i]
        if t2_idx - t1_idx < MIN_BARS_BETWEEN:
            continue
        t1, t2 = low[t1_idx], low[t2_idx]
        if abs(t1 - t2) / max(abs(t1), abs(t2)) > PEAK_TOLERANCE:
            continue
        peaks = [j for j in sh_idx if t1_idx < j < t2_idx]
        if not peaks:
            continue
        peak_idx = peaks[int(np.argmax([high[j] for j in peaks]))]
        peak_p = high[peak_idx]
        pattern_h = peak_p - min(t1, t2)
        if pattern_h <= 0:
            continue
        # NOTE: start search at t2_idx + PIVOT_DISTANCE so the second trough
        # is confirmed by find_peaks(distance=PIVOT_DISTANCE) before entry.
        for j in range(t2_idx + PIVOT_DISTANCE, min(t2_idx + ENTRY_SEARCH_WINDOW, n)):
            if close[j] > peak_p:
                entry = close[j]
                stop = min(t1, t2) - STOP_ATR_MULT * atr.iloc[j]
                risk = entry - stop
                if risk <= 0:
                    break
                target = entry + pattern_h
                if (target - entry) < risk:
                    target = entry + risk
                make(j, "long", entry, stop, target, "double_bottom_long")
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
    print(f"STR-U Double Top/Bottom Phase 1A ({asset_type})")
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
    ap = argparse.ArgumentParser(description="STR-U Double Top/Bottom Scanner")
    ap.add_argument("--backtest", action="store_true")
    ap.add_argument("--crypto", action="store_true")
    args = ap.parse_args()
    if args.backtest:
        if args.crypto:
            symbols = ["BTC", "ETH", "SOL", "OP", "ARB", "AVAX", "DOGE", "LINK"]
            print("=== STR-U Phase 1A Backtest (Crypto) ===\n")
            result = run_phase1a(symbols, "crypto")
        else:
            symbols = ["SPY", "QQQ", "AAPL", "NVDA", "TSLA", "AMZN", "MSFT", "GOOGL",
                       "META", "AMD", "NFLX", "JPM", "BAC", "XOM", "CVX", "PFE", "UNH", "COST"]
            print("=== STR-U Phase 1A Backtest (Stocks) ===\n")
            result = run_phase1a(symbols, "stock")
            if len(result) > 0:
                out_path = Path(__file__).parent.parent / "results" / "STR-U-stocks-phase1a.csv"
                out_path.parent.mkdir(parents=True, exist_ok=True)
                result.to_csv(out_path, index=False)
                print(f"\nResults saved to {out_path}")
    else:
        print(__doc__)
