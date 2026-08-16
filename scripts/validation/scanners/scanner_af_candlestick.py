#!/usr/bin/env python3
"""
scanner_af_candlestick.py
=========================
HermesForge STR-AF: Candlestick Reversal Patterns

Detects classic candlestick reversal patterns and trades them as reversals.

Patterns (body = abs(close-open), upper_wick = high - max(open,close),
          lower_wick = min(open,close) - low):

  Bullish:
    - Hammer (1-bar): small body near top, long lower wick (>= 2x body)
    - Piercing Line (2-bar): down candle then bullish candle opening below
      prior low but closing above prior midpoint
    - Morning Star (3-bar): down candle, small-body gap-down candle, bullish
      candle closing well into first candle's body
    - Three White Soldiers (3-bar): three consecutive rising bullish candles

  Bearish:
    - Shooting Star (1-bar): small body near bottom, long upper wick (>= 2x body)
    - Dark Cloud Cover (2-bar): up candle then bearish candle opening above
      prior high but closing below prior midpoint
    - Evening Star (3-bar): up candle, small-body gap-up candle, bearish candle
      closing well into first candle's body
    - Three Black Crows (3-bar): three consecutive falling bearish candles

Entry on pattern completion bar close.
Stop: 1 ATR(14).
Target: 2R.
Time stop: 10 bars.

Long-only for stocks (only bullish patterns fire on stocks).

Dependencies: pandas, numpy
"""

import sys
import pandas as pd
import numpy as np
from pathlib import Path

STRATEGY_ID = "STR-AF-candlestick"
STRATEGY_NAME = "Candlestick Reversal Patterns"
STRATEGY_VERSION = "1.0"
MAX_HOLD_BARS = 10
TARGET_RR = 2.0
STOP_ATR_MULT = 1.0
ATR_PERIOD = 14


def _atr(df: pd.DataFrame, period: int = ATR_PERIOD) -> pd.Series:
    high, low, close = df["high"], df["low"], df["close"]
    prev_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs(),
    ], axis=1).max(axis=1)
    return tr.ewm(alpha=1 / period, adjust=False).mean()


def _candle_props(o, c, h, l):
    body = abs(c - o)
    upper_wick = h - max(o, c)
    lower_wick = min(o, c) - l
    rng = (h - l) if (h - l) > 0 else 1e-9
    return body, upper_wick, lower_wick, rng


def _detect_patterns(df: pd.DataFrame) -> pd.DataFrame:
    """Return a DataFrame with boolean columns for each pattern, indexed like df."""
    o = df["open"].values
    c = df["close"].values
    h = df["high"].values
    l = df["low"].values
    n = len(df)
    bullish = {k: np.zeros(n, dtype=bool) for k in
               ["hammer", "piercing", "morning_star", "three_white_soldiers"]}
    bearish = {k: np.zeros(n, dtype=bool) for k in
               ["shooting_star", "dark_cloud", "evening_star", "three_black_crows"]}

    for i in range(n):
        body, uw, lw, rng = _candle_props(o[i], c[i], h[i], l[i])
        is_bull = c[i] > o[i]
        is_bear = c[i] < o[i]
        small_body = body < rng * 0.35

        # ── 1-bar patterns ──
        if lw >= 2 * body and body > 0 and (uw < body):
            bullish["hammer"][i] = True
        if uw >= 2 * body and body > 0 and (lw < body):
            bearish["shooting_star"][i] = True

        # ── 2-bar patterns ──
        if i >= 1:
            p_body, p_uw, p_lw, p_rng = _candle_props(o[i-1], c[i-1], h[i-1], l[i-1])
            p_mid = (o[i-1] + c[i-1]) / 2
            # Piercing Line: prior bearish, current bullish, opens below prior low,
            # closes above prior midpoint but below prior open
            if c[i-1] < o[i-1] and c[i] > o[i] and o[i] < l[i-1] and c[i] > p_mid and c[i] < o[i-1]:
                bullish["piercing"][i] = True
            # Dark Cloud Cover: prior bullish, current bearish, opens above prior high,
            # closes below prior midpoint but above prior close
            if c[i-1] > o[i-1] and c[i] < o[i] and o[i] > h[i-1] and c[i] < p_mid and c[i] > c[i-1]:
                bearish["dark_cloud"][i] = True

        # ── 3-bar patterns ──
        if i >= 2:
            b0_body, _, _, _ = _candle_props(o[i-2], c[i-2], h[i-2], l[i-2])
            b1_body, _, _, b1_rng = _candle_props(o[i-1], c[i-1], h[i-1], l[i-1])
            b2_body, _, _, b2_rng = _candle_props(o[i], c[i], h[i], l[i])
            b0_bear = c[i-2] < o[i-2]
            b0_bull = c[i-2] > o[i-2]
            b2_bull = c[i] > o[i]
            b2_bear = c[i] < o[i]
            b1_small = b1_body < b1_rng * 0.4
            # Morning Star: bearish, small gap-down, bullish closing into b0 body
            if b0_bear and b1_small and b2_bull and c[i] > (o[i-2] + c[i-2]) / 2:
                bullish["morning_star"][i] = True
            # Evening Star: bullish, small gap-up, bearish closing into b0 body
            if b0_bull and b1_small and b2_bear and c[i] < (o[i-2] + c[i-2]) / 2:
                bearish["evening_star"][i] = True
            # Three White Soldiers: three consecutive rising bullish candles
            if (c[i-2] > o[i-2] and c[i-1] > o[i-1] and c[i] > o[i] and
                    c[i-1] > c[i-2] and c[i] > c[i-1] and
                    o[i-1] > o[i-2] and o[i] > o[i-1]):
                bullish["three_white_soldiers"][i] = True
            # Three Black Crows: three consecutive falling bearish candles
            if (c[i-2] < o[i-2] and c[i-1] < o[i-1] and c[i] < o[i] and
                    c[i-1] < c[i-2] and c[i] < c[i-1] and
                    o[i-1] < o[i-2] and o[i] < o[i-1]):
                bearish["three_black_crows"][i] = True

    out = pd.DataFrame(index=df.index)
    for k, v in bullish.items():
        out[k] = v
    for k, v in bearish.items():
        out[k] = v
    out["atr"] = _atr(df).values
    return out


BULLISH_PATTERNS = ["hammer", "piercing", "morning_star", "three_white_soldiers"]
BEARISH_PATTERNS = ["shooting_star", "dark_cloud", "evening_star", "three_black_crows"]


def scan(df: pd.DataFrame, ticker: str, long_only: bool = False) -> list:
    if len(df) < max(ATR_PERIOD + 5, 5):
        return []
    pat = _detect_patterns(df)
    signals = []
    for i in range(len(df)):
        atr = pat["atr"].iloc[i]
        if pd.isna(atr) or atr <= 0:
            continue
        close = df["close"].iloc[i]
        date = df.index[i]

        # Bullish patterns → LONG
        for pname in BULLISH_PATTERNS:
            if pat[pname].iloc[i]:
                entry_price = close
                stop_price = entry_price - STOP_ATR_MULT * atr
                risk = entry_price - stop_price
                if risk <= 0:
                    continue
                target_price = entry_price + risk * TARGET_RR
                signals.append({
                    "date": date,
                    "ticker": ticker,
                    "strategy_id": STRATEGY_ID,
                    "strategy_name": STRATEGY_NAME,
                    "strategy_version": STRATEGY_VERSION,
                    "direction": "long",
                    "entry_price": entry_price,
                    "stop_price": stop_price,
                    "target_price": target_price,
                    "atr": atr,
                    "signal_type": f"candle_{pname}_long",
                })

        # Bearish patterns → SHORT (only if not long_only)
        if not long_only:
            for pname in BEARISH_PATTERNS:
                if pat[pname].iloc[i]:
                    entry_price = close
                    stop_price = entry_price + STOP_ATR_MULT * atr
                    risk = stop_price - entry_price
                    if risk <= 0:
                        continue
                    target_price = entry_price - risk * TARGET_RR
                    signals.append({
                        "date": date,
                        "ticker": ticker,
                        "strategy_id": STRATEGY_ID,
                        "strategy_name": STRATEGY_NAME,
                        "strategy_version": STRATEGY_VERSION,
                        "direction": "short",
                        "entry_price": entry_price,
                        "stop_price": stop_price,
                        "target_price": target_price,
                        "atr": atr,
                        "signal_type": f"candle_{pname}_short",
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
    r = ((exit_price - entry_price) / risk) if direction == "long" else ((entry_price - exit_price) / risk)
    if risk <= 0:
        r = 0.0
    return {"exit_type": "time", "exit_price": exit_price,
            "bars_held": exit_idx - entry_idx, "r_multiple": round(r, 3)}


def run_backtest(df: pd.DataFrame, ticker: str, long_only: bool = False) -> list:
    signals = scan(df, ticker, long_only=long_only)
    if not signals:
        return []
    trades = []
    for sig in signals:
        try:
            target_date = pd.Timestamp(sig["date"])
            entry_idx = df.index.get_loc(df.index[df.index == target_date][0])
        except (KeyError, ValueError, IndexError, TypeError):
            continue
        if entry_idx + 1 >= len(df):
            continue
        exit_result = _walk_forward_exit(
            df, entry_idx, sig["direction"],
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

    df_trades = pd.DataFrame(all_trades)
    _print_summary(df_trades, asset_type)
    return df_trades


def _print_summary(df: pd.DataFrame, asset_type: str):
    print(f"\n{'='*60}")
    print(f"STR-AF Candlestick Reversal Phase 1A Backtest ({asset_type})")
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
    print(f"\nBy pattern (signal_type):")
    for st in sorted(df["signal_type"].unique()):
        s = df[df["signal_type"] == st]
        if len(s) > 0:
            print(f"  {st}: {len(s)} trades, WR={((s['r_multiple'] > 0).mean() * 100):.1f}%, "
                  f"avg R={s['r_multiple'].mean():.3f}")
    pos_r = df[df["r_multiple"] > 0]["r_multiple"].sum()
    neg_r = abs(df[df["r_multiple"] < 0]["r_multiple"].sum())
    pf = pos_r / neg_r if neg_r > 0 else float('inf')
    print(f"\nProfit factor: {pf:.2f}")
    print(f"\nBy symbol:")
    for sym in sorted(df["symbol"].unique()):
        s = df[df["symbol"] == sym]
        print(f"  {sym}: {len(s)} trades, WR={((s['r_multiple'] > 0).mean() * 100):.1f}%, "
              f"avg R={s['r_multiple'].mean():.3f}, sum R={s['r_multiple'].sum():.3f}")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="STR-AF Candlestick Reversal Scanner")
    ap.add_argument("--backtest", action="store_true", help="Run Phase 1A backtest")
    ap.add_argument("--crypto", action="store_true", help="Backtest crypto instead of stocks")
    args = ap.parse_args()
    if args.backtest:
        if args.crypto:
            symbols = ["BTC", "ETH", "SOL", "OP", "ARB", "AVAX", "DOGE", "LINK"]
            print("=== STR-AF Phase 1A Backtest (Crypto) ===\n")
            result = run_phase1a(symbols, "crypto")
        else:
            symbols = [
                "SPY", "QQQ", "AAPL", "NVDA", "TSLA", "AMZN", "MSFT", "GOOGL", "META",
                "AMD", "NFLX", "JPM", "BAC", "XOM", "CVX", "PFE", "UNH", "COST",
            ]
            print("=== STR-AF Phase 1A Backtest (Stocks) ===\n")
            result = run_phase1a(symbols, "stock")
            if len(result) > 0:
                out_path = Path(__file__).parent.parent / "results" / "STR-AF-stocks-phase1a.csv"
                result.to_csv(out_path, index=False)
                print(f"\nResults saved to {out_path}")
    else:
        print(__doc__)
