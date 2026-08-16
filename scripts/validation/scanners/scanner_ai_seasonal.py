#!/usr/bin/env python3
"""
scanner_ai_seasonal.py
======================
HermesForge STR-AI: Seasonal Tendency Strategy

Compute historical monthly returns for each ticker. Enter on the first trading
day of months that have historically shown a strong directional bias.

Signal Rules:
  LONG:  enter on first trading day of months with historically >60% positive
         return rate
  SHORT: enter on first trading day of months with historically >60% negative
         return rate

"Lookback of all available data" is implemented with an EXPANDING window —
at any point in time we use only completed prior months to compute the
positive/negative rate for each calendar month. This avoids lookahead bias.

Entry on first bar of qualifying month.
Stop: 2 ATR(14).
Target: 3R.
Time stop: 20 bars.

Long-only for stocks.

Dependencies: pandas, numpy
"""

import sys
import pandas as pd
import numpy as np
from pathlib import Path

STRATEGY_ID = "STR-AI-seasonal"
STRATEGY_NAME = "Seasonal Tendency"
STRATEGY_VERSION = "1.0"
MAX_HOLD_BARS = 20
TARGET_RR = 3.0
STOP_ATR_MULT = 2.0
ATR_PERIOD = 14
POS_THRESHOLD = 0.60
NEG_THRESHOLD = 0.60


def _atr(df: pd.DataFrame, period: int = ATR_PERIOD) -> pd.Series:
    high, low, close = df["high"], df["low"], df["close"]
    prev_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs(),
    ], axis=1).max(axis=1)
    return tr.ewm(alpha=1 / period, adjust=False).mean()


def _monthly_returns(df: pd.DataFrame) -> pd.DataFrame:
    """Resample to month-end and compute monthly % returns."""
    monthly = df["close"].resample("ME").last().dropna()
    rets = monthly.pct_change().dropna()
    out = pd.DataFrame({"month_end": rets.index, "monthly_return": rets.values})
    out["year"] = out["month_end"].dt.year
    out["calendar_month"] = out["month_end"].dt.month
    return out


def _first_bar_of_month(df: pd.DataFrame) -> pd.Series:
    """Boolean series: True on the first trading bar of each calendar month."""
    months = df.index.to_period("M")
    first_mask = pd.Series(months, index=df.index).ne(pd.Series(months, index=df.index).shift(1))
    return first_mask.fillna(True)


def _expanding_month_pos_rate(df: pd.DataFrame) -> pd.DataFrame:
    """For each bar, compute the historical positive-rate of the current
    calendar month using ONLY completed prior months (expanding, no lookahead).
    Returns a DataFrame with columns: pos_rate, neg_rate, n_obs.
    """
    mr = _monthly_returns(df)
    # Map each month_end to its completed-month record
    # For each bar in df, the "current month" is its calendar month.
    # We use all completed months BEFORE the bar's month.
    cal_month = df.index.month
    cur_year_month = df.index.to_period("M")

    pos_rate = np.zeros(len(df))
    neg_rate = np.zeros(len(df))
    n_obs = np.zeros(len(df))

    # Precompute per-calendar-month cumulative stats sorted by time
    mr_sorted = mr.sort_values("month_end").reset_index(drop=True)
    for i, idx in enumerate(df.index):
        cm = cal_month[i]
        cur_ym = cur_year_month[i]
        # completed months of this calendar month, strictly before current month
        mask = (mr_sorted["calendar_month"] == cm) & (mr_sorted["month_end"].dt.to_period("M") < cur_ym)
        hist = mr_sorted.loc[mask, "monthly_return"]
        n = len(hist)
        n_obs[i] = n
        if n == 0:
            pos_rate[i] = np.nan
            neg_rate[i] = np.nan
        else:
            pos_rate[i] = (hist > 0).mean()
            neg_rate[i] = (hist < 0).mean()

    return pd.DataFrame({"pos_rate": pos_rate, "neg_rate": neg_rate, "n_obs": n_obs}, index=df.index)


def scan(df: pd.DataFrame, ticker: str, long_only: bool = False) -> list:
    if len(df) < 60:
        return []
    atr_s = _atr(df)
    first_bar = _first_bar_of_month(df)
    rates = _expanding_month_pos_rate(df)

    signals = []
    for i in range(len(df)):
        if not first_bar.iloc[i]:
            continue
        atr = atr_s.iloc[i]
        if pd.isna(atr) or atr <= 0:
            continue
        pr = rates["pos_rate"].iloc[i]
        nr = rates["neg_rate"].iloc[i]
        n = rates["n_obs"].iloc[i]
        if n < 5:  # need a minimum sample
            continue
        close = df["close"].iloc[i]
        date = df.index[i]

        # LONG: positive rate > threshold
        if not pd.isna(pr) and pr > POS_THRESHOLD:
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
                "pos_rate": pr,
                "n_obs": n,
                "calendar_month": date.month,
                "signal_type": f"seasonal_long_m{date.month:02d}",
            })

        # SHORT: negative rate > threshold
        if not long_only and not pd.isna(nr) and nr > NEG_THRESHOLD:
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
                "neg_rate": nr,
                "n_obs": n,
                "calendar_month": date.month,
                "signal_type": f"seasonal_short_m{date.month:02d}",
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

    df_trades = pd.DataFrame(all_trades)
    _print_summary(df_trades, asset_type)
    return df_trades


def _print_summary(df: pd.DataFrame, asset_type: str):
    print(f"\n{'='*60}")
    print(f"STR-AI Seasonal Tendency Phase 1A Backtest ({asset_type})")
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
    print(f"\nBy calendar month (signal_type):")
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
    ap = argparse.ArgumentParser(description="STR-AI Seasonal Tendency Scanner")
    ap.add_argument("--backtest", action="store_true", help="Run Phase 1A backtest")
    ap.add_argument("--crypto", action="store_true", help="Backtest crypto instead of stocks")
    args = ap.parse_args()
    if args.backtest:
        if args.crypto:
            symbols = ["BTC", "ETH", "SOL", "OP", "ARB", "AVAX", "DOGE", "LINK"]
            print("=== STR-AI Phase 1A Backtest (Crypto) ===\n")
            result = run_phase1a(symbols, "crypto")
        else:
            symbols = [
                "SPY", "QQQ", "AAPL", "NVDA", "TSLA", "AMZN", "MSFT", "GOOGL", "META",
                "AMD", "NFLX", "JPM", "BAC", "XOM", "CVX", "PFE", "UNH", "COST",
            ]
            print("=== STR-AI Phase 1A Backtest (Stocks) ===\n")
            result = run_phase1a(symbols, "stock")
            if len(result) > 0:
                out_path = Path(__file__).parent.parent / "results" / "STR-AI-stocks-phase1a.csv"
                result.to_csv(out_path, index=False)
                print(f"\nResults saved to {out_path}")
    else:
        print(__doc__)
