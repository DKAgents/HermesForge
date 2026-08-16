#!/usr/bin/env python3
"""
scanner_t_head_shoulders.py
==========================
HermesForge STR-T: Head and Shoulders Reversal

Detect a 3-peak pattern where the middle peak (head) is the highest and the
left/right peaks (shoulders) are roughly equal (within 3% tolerance). The
neckline is the line connecting the two troughs between the shoulders.

Signal rules:
  Regular H&S (bearish): entry on close below neckline.
    Stop: 1 ATR beyond the head (above).
    Target: head height (head - neckline at head) projected down from the
            neckline at the breakout bar.
  Inverse H&S (bullish): entry on close above neckline.
    Stop: 1 ATR beyond the head (below).
    Target: head height projected up from the neckline at the breakout bar.
  Long-only for stocks.

Dependencies: pandas, numpy, scipy
"""

import sys
import pandas as pd
import numpy as np
from pathlib import Path
from scipy.signal import find_peaks

STRATEGY_ID = "STR-T-head-shoulders"
STRATEGY_NAME = "Head and Shoulders Reversal"
STRATEGY_VERSION = "1.0"
MAX_HOLD_BARS = 25
TARGET_RR = None           # target set per-trade from pattern height
STOP_ATR_MULT = 1.0
SHOULDER_TOLERANCE = 0.03  # 3%
PIVOT_DISTANCE = 5
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

    # ── Regular H&S (bearish) ──
    # 3 swing highs: L (left shoulder), H (head), R (right shoulder)
    # H highest; L and R within SHOULDER_TOLERANCE.
    # trough1 = swing low between L and H; trough2 = swing low between H and R.
    for i in range(2, len(sh_idx)):
        L_idx, H_idx, R_idx = sh_idx[i - 2], sh_idx[i - 1], sh_idx[i]
        Lp, Hp, Rp = high[L_idx], high[H_idx], high[R_idx]
        if not (Hp > Lp and Hp > Rp):
            continue
        if abs(Lp - Rp) / max(Lp, Rp) > SHOULDER_TOLERANCE:
            continue
        # troughs
        t1 = [j for j in sl_idx if L_idx < j < H_idx]
        t2 = [j for j in sl_idx if H_idx < j < R_idx]
        if not t1 or not t2:
            continue
        t1_idx = t1[-1]
        t2_idx = t2[0]
        t1p = low[t1_idx]
        t2p = low[t2_idx]
        # neckline through (t1_idx, t1p) and (t2_idx, t2p)
        dx = t2_idx - t1_idx
        if dx == 0:
            continue
        slope = (t2p - t1p) / dx
        def neckline(x):
            return t1p + slope * (x - t1_idx)

        # entry: first close after R_idx below neckline
        # NOTE: start search at R_idx + PIVOT_DISTANCE so the right-shoulder
        # pivot is confirmed by find_peaks(distance=PIVOT_DISTANCE) before entry.
        for j in range(R_idx + PIVOT_DISTANCE, min(R_idx + ENTRY_SEARCH_WINDOW, n)):
            nl = neckline(j)
            if close[j] < nl:
                entry = close[j]
                stop = Hp + STOP_ATR_MULT * atr.iloc[j]
                risk = stop - entry
                if risk <= 0:
                    break
                head_h = Hp - neckline(H_idx)
                target = entry - head_h  # projected down from neckline at break
                # ensure target is at least 1R away; if not, use 1R floor
                if (entry - target) < risk:
                    target = entry - risk
                if not long_only:
                    make(j, "short", entry, stop, target, "head_shoulders_short")
                break

    # ── Inverse H&S (bullish) ──
    for i in range(2, len(sl_idx)):
        L_idx, H_idx, R_idx = sl_idx[i - 2], sl_idx[i - 1], sl_idx[i]
        Lp, Hp, Rp = low[L_idx], low[H_idx], low[R_idx]
        if not (Hp < Lp and Hp < Rp):
            continue
        if abs(Lp - Rp) / max(abs(Lp), abs(Rp)) > SHOULDER_TOLERANCE:
            continue
        p1 = [j for j in sh_idx if L_idx < j < H_idx]
        p2 = [j for j in sh_idx if H_idx < j < R_idx]
        if not p1 or not p2:
            continue
        p1_idx = p1[-1]
        p2_idx = p2[0]
        p1p = high[p1_idx]
        p2p = high[p2_idx]
        dx = p2_idx - p1_idx
        if dx == 0:
            continue
        slope = (p2p - p1p) / dx
        def neckline(x):
            return p1p + slope * (x - p1_idx)

        # NOTE: start search at R_idx + PIVOT_DISTANCE so the right-shoulder
        # pivot is confirmed by find_peaks(distance=PIVOT_DISTANCE) before entry.
        for j in range(R_idx + PIVOT_DISTANCE, min(R_idx + ENTRY_SEARCH_WINDOW, n)):
            nl = neckline(j)
            if close[j] > nl:
                entry = close[j]
                stop = Hp - STOP_ATR_MULT * atr.iloc[j]
                risk = entry - stop
                if risk <= 0:
                    break
                head_h = neckline(H_idx) - Hp
                target = entry + head_h
                if (target - entry) < risk:
                    target = entry + risk
                make(j, "long", entry, stop, target, "inv_head_shoulders_long")
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
        # compute R for target exits (variable R since target isn't always 3R)
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
    print(f"STR-T Head and Shoulders Phase 1A ({asset_type})")
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
    ap = argparse.ArgumentParser(description="STR-T Head and Shoulders Scanner")
    ap.add_argument("--backtest", action="store_true")
    ap.add_argument("--crypto", action="store_true")
    args = ap.parse_args()
    if args.backtest:
        if args.crypto:
            symbols = ["BTC", "ETH", "SOL", "OP", "ARB", "AVAX", "DOGE", "LINK"]
            print("=== STR-T Phase 1A Backtest (Crypto) ===\n")
            result = run_phase1a(symbols, "crypto")
        else:
            symbols = ["SPY", "QQQ", "AAPL", "NVDA", "TSLA", "AMZN", "MSFT", "GOOGL",
                       "META", "AMD", "NFLX", "JPM", "BAC", "XOM", "CVX", "PFE", "UNH", "COST"]
            print("=== STR-T Phase 1A Backtest (Stocks) ===\n")
            result = run_phase1a(symbols, "stock")
            if len(result) > 0:
                out_path = Path(__file__).parent.parent / "results" / "STR-T-stocks-phase1a.csv"
                out_path.parent.mkdir(parents=True, exist_ok=True)
                result.to_csv(out_path, index=False)
                print(f"\nResults saved to {out_path}")
    else:
        print(__doc__)
