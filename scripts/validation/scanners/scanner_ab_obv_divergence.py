#!/usr/bin/env python3
"""
scanner_ab_obv_divergence.py
============================
HermesForge STR-AB: OBV Divergence Strategy

Compute OBV (cumulative volume where up days add volume, down days subtract).

  LONG:  price makes a lower low but OBV makes a higher low (bullish divergence).
         Entry on the bar where divergence is confirmed (price closes above the
         prior swing low).
  SHORT: price makes a higher high but OBV makes a lower high (bearish divergence).
         Entry on the bar where price closes below the prior swing high.

  Entry on confirmation bar close.
  Stop: 1.5 ATR(14) below the divergence low (long) / above the divergence high (short).
  Target: 3R.
  Time stop: 20 bars.
  Long-only for stocks.

Swing detection: pivot lows/highs identified using a 5-bar window (2 bars on each side).

Dependencies: pandas, numpy
"""

import sys
import pandas as pd
import numpy as np
from pathlib import Path

STRATEGY_ID = "STR-AB-obv-divergence"
STRATEGY_NAME = "OBV Divergence"
STRATEGY_VERSION = "1.0"
MAX_HOLD_BARS = 20
TARGET_RR = 3.0
STOP_ATR_MULT = 1.5
SWING_WINDOW = 2  # bars on each side for pivot detection
MIN_BETWEEN_PIVOTS = 5


def _compute_atr(high: pd.Series, low: pd.Series, close: pd.Series,
                  period: int = 14) -> pd.Series:
    prev_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs(),
    ], axis=1).max(axis=1)
    return tr.ewm(alpha=1.0 / period, adjust=False).mean()


def _compute_obv(close: pd.Series, volume: pd.Series) -> pd.Series:
    direction = np.sign(close.diff())
    direction.iloc[0] = 0
    return (direction * volume).cumsum()


def _find_pivots(series: pd.Series, window: int = SWING_WINDOW, kind: str = "low") -> list:
    """Find pivot lows/highs. Returns list of (index_position, value).

    A pivot low at bar i means arr[i] is <= all bars in [i-window, i+window]
    and strictly < at least one bar on each side. Symmetric for pivot high.
    """
    pivots = []
    arr = series.values
    n = len(arr)
    for i in range(window, n - window):
        val = arr[i]
        if np.isnan(val):
            continue
        left = arr[i - window:i]      # window bars to the left
        right = arr[i + 1:i + 1 + window]  # window bars to the right
        # Skip if any neighbor is NaN
        if np.any(np.isnan(left)) or np.any(np.isnan(right)):
            continue
        if kind == "low":
            is_pivot = (np.all(left >= val) and np.all(right >= val) and
                        (np.any(left > val) or np.any(right > val)))
        else:  # high
            is_pivot = (np.all(left <= val) and np.all(right <= val) and
                        (np.any(left < val) or np.any(right < val)))
        if is_pivot:
            pivots.append((i, val))
    return pivots


def scan(df: pd.DataFrame, ticker: str, long_only: bool = False) -> list:
    if len(df) < 60:
        return []

    df = df.copy()
    df.columns = df.columns.str.lower()
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index)
    df.sort_index(inplace=True)

    close = df["close"]
    high = df["high"]
    low = df["low"]
    volume = df["volume"]

    obv = _compute_obv(close, volume)
    atr = _compute_atr(high, low, close)
    close_arr = close.values.astype(float)
    low_arr = low.values.astype(float)
    high_arr = high.values.astype(float)
    obv_arr = obv.values.astype(float)
    atr_arr = atr.values.astype(float)

    signals = []
    min_start = max(30, SWING_WINDOW * 2 + 1)

    # Find pivot lows in price and OBV
    price_pivot_lows = _find_pivots(low, SWING_WINDOW, "low")
    obv_pivot_lows = _find_pivots(pd.Series(obv_arr, index=df.index), SWING_WINDOW, "low")
    price_pivot_highs = _find_pivots(high, SWING_WINDOW, "high")
    obv_pivot_highs = _find_pivots(pd.Series(obv_arr, index=df.index), SWING_WINDOW, "high")

    # Map OBV pivot positions (use nearest within tolerance)
    def _nearest_obv_pivot(price_pivot_idx, obv_pivots, tol=3):
        for op_idx, op_val in obv_pivots:
            if abs(op_idx - price_pivot_idx) <= tol:
                return op_idx, op_val
        return None

    # ── LONG: bullish divergence ──
    # For each pair of consecutive price pivot lows where second is lower,
    # check if corresponding OBV pivot lows show higher low.
    for p in range(1, len(price_pivot_lows)):
        p1_idx, p1_low = price_pivot_lows[p - 1]
        p2_idx, p2_low = price_pivot_lows[p]
        if p2_idx - p1_idx < MIN_BETWEEN_PIVOTS:
            continue
        if p2_low >= p1_low:
            continue  # not a lower low
        # OBV pivots near these
        obv1 = _nearest_obv_pivot(p1_idx, obv_pivot_lows)
        obv2 = _nearest_obv_pivot(p2_idx, obv_pivot_lows)
        if obv1 is None or obv2 is None:
            continue
        obv1_val = obv1[1]
        obv2_val = obv2[1]
        if obv2_val <= obv1_val:
            continue  # not a higher low in OBV
        # Bullish divergence confirmed. Entry = first close above p2_low after p2_idx.
        if np.isnan(atr_arr[p2_idx]):
            continue
        entry_idx = None
        for j in range(p2_idx + SWING_WINDOW + 1, len(df)):
            if np.isnan(close_arr[j]) or np.isnan(atr_arr[j]):
                continue
            if close_arr[j] > p2_low:
                entry_idx = j
                break
        if entry_idx is None:
            continue
        entry_price = close_arr[entry_idx]
        # Stop 1.5 ATR below the divergence low
        stop_price = p2_low - STOP_ATR_MULT * atr_arr[p2_idx]
        risk = entry_price - stop_price
        if risk <= 0:
            continue
        target_price = entry_price + risk * TARGET_RR
        ts = df.index[entry_idx]
        signals.append({
            "date": ts,
            "ticker": ticker,
            "strategy_id": STRATEGY_ID,
            "strategy_name": STRATEGY_NAME,
            "strategy_version": STRATEGY_VERSION,
            "direction": "long",
            "entry_price": round(entry_price, 4),
            "stop_price": round(stop_price, 4),
            "target_price": round(target_price, 4),
            "divergence_low": round(p2_low, 4),
            "obv_low1": round(obv1_val, 2),
            "obv_low2": round(obv2_val, 2),
            "signal_type": "obv_bullish_divergence",
        })

    # ── SHORT: bearish divergence ──
    if not long_only:
        for p in range(1, len(price_pivot_highs)):
            p1_idx, p1_high = price_pivot_highs[p - 1]
            p2_idx, p2_high = price_pivot_highs[p]
            if p2_idx - p1_idx < MIN_BETWEEN_PIVOTS:
                continue
            if p2_high <= p1_high:
                continue  # not a higher high
            obv1 = _nearest_obv_pivot(p1_idx, obv_pivot_highs)
            obv2 = _nearest_obv_pivot(p2_idx, obv_pivot_highs)
            if obv1 is None or obv2 is None:
                continue
            obv1_val = obv1[1]
            obv2_val = obv2[1]
            if obv2_val >= obv1_val:
                continue  # not a lower high in OBV
            if np.isnan(atr_arr[p2_idx]):
                continue
            entry_idx = None
            for j in range(p2_idx + SWING_WINDOW + 1, len(df)):
                if np.isnan(close_arr[j]) or np.isnan(atr_arr[j]):
                    continue
                if close_arr[j] < p2_high:
                    entry_idx = j
                    break
            if entry_idx is None:
                continue
            entry_price = close_arr[entry_idx]
            stop_price = p2_high + STOP_ATR_MULT * atr_arr[p2_idx]
            risk = stop_price - entry_price
            if risk <= 0:
                continue
            target_price = entry_price - risk * TARGET_RR
            ts = df.index[entry_idx]
            signals.append({
                "date": ts,
                "ticker": ticker,
                "strategy_id": STRATEGY_ID,
                "strategy_name": STRATEGY_NAME,
                "strategy_version": STRATEGY_VERSION,
                "direction": "short",
                "entry_price": round(entry_price, 4),
                "stop_price": round(stop_price, 4),
                "target_price": round(target_price, 4),
                "divergence_high": round(p2_high, 4),
                "obv_high1": round(obv1_val, 2),
                "obv_high2": round(obv2_val, 2),
                "signal_type": "obv_bearish_divergence",
            })

    return signals


def _walk_forward_exit(df: pd.DataFrame, entry_idx: int, direction: str,
                       entry_price: float, stop_price: float, target_price: float,
                       max_bars: int = MAX_HOLD_BARS) -> dict:
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

    exit_idx = min(entry_idx + max_bars, n - 1)
    exit_price = df.iloc[exit_idx]["close"]
    risk = (entry_price - stop_price) if direction == "long" else (stop_price - entry_price)
    if risk <= 0:
        r = 0.0
    else:
        r = ((exit_price - entry_price) / risk) if direction == "long" \
            else ((entry_price - exit_price) / risk)
    return {"exit_type": "time", "exit_price": round(exit_price, 4),
            "bars_held": max_bars, "r_multiple": round(r, 3)}


def run_backtest(df: pd.DataFrame, ticker: str, long_only: bool = False) -> list:
    signals = scan(df, ticker, long_only=long_only)
    if not signals:
        return []

    df = df.copy()
    df.columns = df.columns.str.lower()
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index)
    df.sort_index(inplace=True)

    trades = []
    for sig in signals:
        target_date = pd.Timestamp(sig["date"])
        try:
            entry_idx = df.index.get_loc(target_date)
        except (KeyError, ValueError, TypeError):
            mask = df.index == target_date
            if not mask.any():
                continue
            entry_idx = df.index.get_loc(df.index[mask][0])

        if isinstance(entry_idx, slice):
            entry_idx = entry_idx.start
        if isinstance(entry_idx, (list, np.ndarray)):
            entry_idx = int(entry_idx[0])
        if entry_idx + 1 >= len(df):
            continue

        exit_result = _walk_forward_exit(
            df, int(entry_idx), sig["direction"],
            sig["entry_price"], sig["stop_price"], sig["target_price"],
        )
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
        df.columns = df.columns.str.lower()

        if len(df) < 50:
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
    print(f"STR-AB OBV Divergence Phase 1A Backtest ({asset_type})")
    print(f"{'='*60}")
    _print_summary(df)
    return df


def _print_summary(df: pd.DataFrame) -> None:
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

    print(f"\nBy symbol:")
    for sym in sorted(df["symbol"].unique()):
        s = df[df["symbol"] == sym]
        print(f"  {sym}: {len(s)} trades, WR={((s['r_multiple'] > 0).mean() * 100):.1f}%, "
              f"avg R={s['r_multiple'].mean():.3f}, sum R={s['r_multiple'].sum():.2f}")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="STR-AB OBV Divergence Scanner")
    ap.add_argument("--backtest", action="store_true", help="Run Phase 1A backtest")
    ap.add_argument("--crypto", action="store_true", help="Backtest crypto instead of stocks")
    args = ap.parse_args()

    if args.backtest:
        if args.crypto:
            crypto_symbols = ["BTC", "ETH", "SOL", "OP", "ARB", "AVAX", "DOGE", "LINK"]
            print("=== STR-AB Phase 1A Backtest (Crypto) ===\n")
            result = run_phase1a(crypto_symbols, "crypto")
        else:
            stock_symbols = [
                "SPY", "QQQ", "AAPL", "NVDA", "TSLA", "AMZN", "MSFT", "GOOGL", "META",
                "AMD", "NFLX", "JPM", "BAC", "XOM", "CVX", "PFE", "UNH", "COST",
            ]
            print("=== STR-AB Phase 1A Backtest (Stocks) ===\n")
            result = run_phase1a(stock_symbols, "stock")
            if len(result) > 0:
                out_path = Path(__file__).parent.parent / "results" / "STR-AB-stocks-phase1a.csv"
                result.to_csv(out_path, index=False)
                print(f"\nResults saved to {out_path}")
    else:
        print(__doc__)
