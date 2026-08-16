#!/usr/bin/env python3
"""
scanner_aj_intermarket.py
=========================
HermesForge STR-AJ: Intermarket Rotation Strategy

Market-wide risk-on/risk-off signal driven by the Dollar (DXY) and the 10-Year
Treasury yield (TNX). When both are falling, conditions are risk-on for equities;
when both are rising, risk-off.

Signal Rules:
  LONG stocks when:
    - DXY 20-day slope < 0 (dollar falling) AND
    - 10Y Treasury yield 20-day slope < 0 (yields falling) AND
    - Stock price above its 50-day SMA (trend filter)
  SHORT/avoid stocks when:
    - DXY 20-day slope > 0 AND yields rising (risk-off)
    (Only generated when not long_only.)

Entry signal: DXY 20-day slope TURNS negative (was >=0, now <0) AND TNX slope
< 0 AND price > 50-day SMA.

Stop: 2 ATR(14).
Target: 3R.
Time stop: 20 bars.

This is a market-wide signal applied to every stock in the universe — each
stock gets its own entry/exit but the trigger is the same intermarket condition.

Dependencies: pandas, numpy, yfinance (with parquet fallback/cache)
"""

import sys
import pandas as pd
import numpy as np
from pathlib import Path

STRATEGY_ID = "STR-AJ-intermarket"
STRATEGY_NAME = "Intermarket Rotation"
STRATEGY_VERSION = "1.0"
MAX_HOLD_BARS = 20
TARGET_RR = 3.0
STOP_ATR_MULT = 2.0
ATR_PERIOD = 14
SMA_PERIOD = 50
SLOPE_WINDOW = 20
DATA_DIR = Path.home() / ".hermes" / "market_data"


def _atr(df: pd.DataFrame, period: int = ATR_PERIOD) -> pd.Series:
    high, low, close = df["high"], df["low"], df["close"]
    prev_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs(),
    ], axis=1).max(axis=1)
    return tr.ewm(alpha=1 / period, adjust=False).mean()


def _slope(series: pd.Series, window: int = SLOPE_WINDOW) -> pd.Series:
    """Rolling linear-regression slope of a series."""
    def _sl(v):
        v = np.asarray(v, dtype=float)
        if np.isnan(v).any() or len(v) < window:
            return np.nan
        x = np.arange(window, dtype=float)
        y = v
        xm, ym = x.mean(), y.mean()
        denom = ((x - xm) ** 2).sum()
        if denom == 0:
            return 0.0
        return ((x - xm) * (y - ym)).sum() / denom
    return series.rolling(window).apply(_sl, raw=True)


# ── Intermarket data fetching ────────────────────────────────────────────────

def fetch_intermarket_data() -> dict:
    """Fetch DXY and 10Y yield (TNX). Try yfinance first; cache to parquet.
    Returns dict {'DXY': df, 'TNX': df} with columns: close, high, low, open.
    """
    cache = {
        "DXY": DATA_DIR / "DXY.parquet",
        "TNX": DATA_DIR / "TNX.parquet",
    }
    tickers = {
        "DXY": ["DX-Y.NYB", "^DXIC", "DXC"],
        "TNX": ["^TNX"],
    }
    out = {}
    for key in ["DXY", "TNX"]:
        loaded = None
        # try cache first
        if cache[key].exists():
            try:
                loaded = pd.read_parquet(cache[key])
                if "Date" in loaded.columns:
                    loaded = loaded.set_index("Date")
                if not isinstance(loaded.index, pd.DatetimeIndex):
                    loaded.index = pd.to_datetime(loaded.index)
                if loaded.index.tz is not None:
                    loaded.index = loaded.index.tz_convert("UTC").tz_localize(None)
                loaded.index = loaded.index.normalize()
            except Exception:
                loaded = None
        if loaded is None or len(loaded) < 60:
            # try yfinance
            try:
                import yfinance as yf
                for sym in tickers[key]:
                    try:
                        t = yf.Ticker(sym)
                        hist = t.history(period="max", auto_adjust=False)
                        if hist is not None and len(hist) > 60:
                            hist = hist.rename(columns=str.lower)
                            # keep only OHLCV
                            cols = [c for c in ["open", "high", "low", "close", "volume"] if c in hist.columns]
                            hist = hist[cols].dropna(subset=["close"])
                            # Normalize index: drop timezone, keep date only so it
                            # aligns with our naive-indexed stock parquets and with
                            # other intermarket series regardless of source tz.
                            if hist.index.tz is not None:
                                hist.index = hist.index.tz_convert("UTC").tz_localize(None)
                            hist.index = hist.index.normalize()
                            # dedupe (some yf symbols return duplicate dates)
                            hist = hist[~hist.index.duplicated(keep="last")]
                            # cache
                            hist.to_parquet(cache[key])
                            print(f"    [intermarket] fetched {key} ({sym}): {len(hist)} bars")
                            loaded = hist
                            break
                    except Exception as e:
                        print(f"    [intermarket] yf {key} ({sym}) failed: {e}")
                        continue
            except ImportError:
                print(f"    [intermarket] yfinance not available for {key}")
        if loaded is None or len(loaded) < 60:
            print(f"    [intermarket] WARNING: no usable data for {key}")
            out[key] = None
        else:
            out[key] = loaded
    return out


# ── Signal computation ──────────────────────────────────────────────────────

def compute_intermarket_signal(dxy: pd.DataFrame, tnx: pd.DataFrame) -> pd.DataFrame:
    """Returns a DataFrame indexed by date with columns:
       dxy_slope, tnx_slope, risk_on (bool), risk_on_trigger (bool, fresh trigger).
    """
    # Align to common dates
    common = dxy.index.intersection(tnx.index)
    if len(common) < 60:
        return pd.DataFrame()
    dxy_c = dxy.loc[common, "close"]
    tnx_c = tnx.loc[common, "close"]
    dxy_sl = _slope(dxy_c, SLOPE_WINDOW)
    tnx_sl = _slope(tnx_c, SLOPE_WINDOW)
    risk_on = (dxy_sl < 0) & (tnx_sl < 0)
    risk_off = (dxy_sl > 0) & (tnx_sl > 0)
    # Trigger: risk_on just turned True (was False/NaN previously)
    risk_on_trigger = risk_on & (~risk_on.shift(1, fill_value=False))
    return pd.DataFrame({
        "dxy_slope": dxy_sl,
        "tnx_slope": tnx_sl,
        "risk_on": risk_on,
        "risk_off": risk_off,
        "risk_on_trigger": risk_on_trigger,
    }, index=common)


def scan(df: pd.DataFrame, ticker: str, long_only: bool = False,
         intermarket: pd.DataFrame = None) -> list:
    """Scan for intermarket-driven signals on a single ticker.
    `intermarket` is the DataFrame from compute_intermarket_signal().
    """
    if intermarket is None or len(intermarket) == 0:
        return []
    if len(df) < SMA_PERIOD + 5:
        return []

    atr_s = _atr(df)
    sma = df["close"].rolling(SMA_PERIOD).mean()

    # Align ticker df to intermarket dates
    common = df.index.intersection(intermarket.index)
    if len(common) < SMA_PERIOD + 5:
        return []
    df_a = df.loc[common]
    im_a = intermarket.loc[common]
    atr_a = atr_s.loc[common]
    sma_a = sma.loc[common]

    signals = []
    for i in range(len(df_a)):
        if not im_a["risk_on_trigger"].iloc[i]:
            continue
        atr = atr_a.iloc[i]
        if pd.isna(atr) or atr <= 0:
            continue
        close = df_a["close"].iloc[i]
        sma_v = sma_a.iloc[i]
        if pd.isna(sma_v):
            continue
        date = df_a.index[i]

        # LONG: risk-on trigger AND price above 50-day SMA
        if close > sma_v:
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
                "sma50": sma_v,
                "dxy_slope": im_a["dxy_slope"].iloc[i],
                "tnx_slope": im_a["tnx_slope"].iloc[i],
                "signal_type": "intermarket_risk_on_long",
            })
        # SHORT: risk-off trigger AND price below 50-day SMA
        elif not long_only and close < sma_v:
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
                "sma50": sma_v,
                "dxy_slope": im_a["dxy_slope"].iloc[i],
                "tnx_slope": im_a["tnx_slope"].iloc[i],
                "signal_type": "intermarket_risk_off_short",
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


def run_backtest(df: pd.DataFrame, ticker: str, long_only: bool = False,
                 intermarket: pd.DataFrame = None) -> list:
    signals = scan(df, ticker, long_only=long_only, intermarket=intermarket)
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
    # Fetch intermarket data once
    print("  Fetching intermarket data (DXY, TNX)...", flush=True)
    im_data = fetch_intermarket_data()
    if im_data.get("DXY") is None or im_data.get("TNX") is None:
        print("  ERROR: Cannot fetch intermarket data — aborting.")
        return pd.DataFrame()
    im_sig = compute_intermarket_signal(im_data["DXY"], im_data["TNX"])
    if len(im_sig) == 0:
        print("  ERROR: Insufficient overlap between DXY and TNX — aborting.")
        return pd.DataFrame()
    n_triggers = int(im_sig["risk_on_trigger"].sum())
    print(f"  Intermarket: {len(im_sig)} aligned days, {n_triggers} risk-on triggers", flush=True)

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
        if len(df) < SMA_PERIOD + 5:
            print(f"    Only {len(df)} bars — skipping")
            continue
        long_only = (asset_type == "stock")
        trades = run_backtest(df, sym, long_only=long_only, intermarket=im_sig)
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
    print(f"STR-AJ Intermarket Rotation Phase 1A Backtest ({asset_type})")
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
    print(f"\nBy symbol:")
    for sym in sorted(df["symbol"].unique()):
        s = df[df["symbol"] == sym]
        print(f"  {sym}: {len(s)} trades, WR={((s['r_multiple'] > 0).mean() * 100):.1f}%, "
              f"avg R={s['r_multiple'].mean():.3f}, sum R={s['r_multiple'].sum():.3f}")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="STR-AJ Intermarket Rotation Scanner")
    ap.add_argument("--backtest", action="store_true", help="Run Phase 1A backtest")
    ap.add_argument("--crypto", action="store_true", help="Backtest crypto instead of stocks")
    args = ap.parse_args()
    if args.backtest:
        if args.crypto:
            symbols = ["BTC", "ETH", "SOL", "OP", "ARB", "AVAX", "DOGE", "LINK"]
            print("=== STR-AJ Phase 1A Backtest (Crypto) ===\n")
            result = run_phase1a(symbols, "crypto")
        else:
            symbols = [
                "SPY", "QQQ", "AAPL", "NVDA", "TSLA", "AMZN", "MSFT", "GOOGL", "META",
                "AMD", "NFLX", "JPM", "BAC", "XOM", "CVX", "PFE", "UNH", "COST",
            ]
            print("=== STR-AJ Phase 1A Backtest (Stocks) ===\n")
            result = run_phase1a(symbols, "stock")
            if len(result) > 0:
                out_path = Path(__file__).parent.parent / "results" / "STR-AJ-stocks-phase1a.csv"
                result.to_csv(out_path, index=False)
                print(f"\nResults saved to {out_path}")
    else:
        print(__doc__)
