#!/usr/bin/env python3
"""
fetch_macro.py — Macro data via yfinance (DXY, Treasury yields, VIX)

Free via yfinance, no API key needed. Fetches:
  - DX-Y.NYB: US Dollar Index
  - ^TNX: 10-Year Treasury Yield
  - ^FVX: 5-Year Treasury Yield  
  - ^IRX: 13-Week T-Bill (proxy for short-term rate)
  - ^VIX: Volatility Index

Caches to ~/.hermes/market_data/macro.parquet
Refreshes if cache > 1 day old.

Usage:
    python3 fetch_macro.py              # fetch/update
    python3 fetch_macro.py --force      # force refresh
"""

import sys
import pathlib
import argparse
import pandas as pd
import yfinance as yf
from datetime import datetime, timezone

CACHE_PATH = pathlib.Path.home() / ".hermes" / "market_data" / "macro.parquet"
VIX_CACHE = pathlib.Path.home() / ".hermes" / "market_data" / "VIXINDEX.parquet"
CACHE_MAX_AGE_HOURS = 12

MACRO_TICKERS = {
    "DX-Y.NYB": "DXY",
    "^TNX": "TNX_10Y",
    "^FVX": "FVX_5Y",
    "^IRX": "IRX_13W",
    "^VIX": "VIX",
}


def fetch_macro(period: str = "2y") -> pd.DataFrame:
    """
    Fetch macro data from yfinance.
    
    Returns DataFrame indexed by date with columns: DXY, TNX_10Y, FVX_5Y, IRX_13W, VIX
    """
    tickers = list(MACRO_TICKERS.keys())
    raw = yf.download(tickers, period=period, progress=False)
    
    # Extract close prices
    if isinstance(raw.columns, pd.MultiIndex):
        close = raw["Close"]
    else:
        close = raw[["Close"]].copy()
        close.columns = [MACRO_TICKERS.get(tickers[0], tickers[0])]
    
    # Rename columns
    renamed = {}
    for col in close.columns:
        renamed[col] = MACRO_TICKERS.get(col, col)
    close = close.rename(columns=renamed)
    
    # Also save VIX to its own parquet for STR-H compatibility
    if "VIX" in close.columns:
        vix_df = close[["VIX"]].dropna()
        vix_df.columns = ["close"]
        VIX_CACHE.parent.mkdir(parents=True, exist_ok=True)
        vix_df.to_parquet(VIX_CACHE)
    
    return close


def load_macro(force: bool = False) -> pd.DataFrame:
    """Load macro data from cache or fetch fresh."""
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    if not force and CACHE_PATH.exists():
        mtime = datetime.fromtimestamp(CACHE_PATH.stat().st_mtime, tz=timezone.utc)
        age = (datetime.now(timezone.utc) - mtime).total_seconds() / 3600
        if age < CACHE_MAX_AGE_HOURS:
            return pd.read_parquet(CACHE_PATH)
    
    df = fetch_macro()
    df.to_parquet(CACHE_PATH)
    print(f"Macro data: {len(df)} rows cached to {CACHE_PATH}", file=sys.stderr)
    return df


def get_yield_curve_signal() -> dict:
    """
    Compute yield curve signal from current macro data.
    
    Returns:
    {
        "tnx": float,          # 10Y yield
        "fvx": float,          # 5Y yield
        "irx": float,          # 13W rate
        "spread_10y_13w": float,  # 10Y - 13W (inversion = recession risk)
        "spread_10y_5y": float,  # 10Y - 5Y
        "inverted": bool,        # 10Y < 13W
        "steepness": str,         # "inverted" / "flat" / "normal" / "steep"
    }
    """
    df = load_macro()
    if df.empty:
        return {}
    
    latest = df.iloc[-1]
    tnx = float(latest.get("TNX_10Y", 0) or 0)
    fvx = float(latest.get("FVX_5Y", 0) or 0)
    irx = float(latest.get("IRX_13W", 0) or 0)
    
    spread_10y_13w = tnx - irx
    spread_10y_5y = tnx - fvx
    inverted = tnx < irx
    
    if inverted:
        steepness = "inverted"
    elif spread_10y_13w < 0.5:
        steepness = "flat"
    elif spread_10y_13w > 2.0:
        steepness = "steep"
    else:
        steepness = "normal"
    
    return {
        "tnx": tnx,
        "fvx": fvx,
        "irx": irx,
        "spread_10y_13w": spread_10y_13w,
        "spread_10y_5y": spread_10y_5y,
        "inverted": inverted,
        "steepness": steepness,
        "date": str(df.index[-1].date()) if hasattr(df.index[-1], 'date') else str(df.index[-1]),
    }


def get_dxy_signal() -> dict:
    """
    Get DXY (dollar index) trend signal.
    
    Returns:
    {
        "current": float,
        "ma_20": float,
        "ma_50": float,
        "trend": str,  # "up" / "down" / "flat"
        "above_50ma": bool,
    }
    """
    df = load_macro()
    if df.empty or "DXY" not in df.columns:
        return {}
    
    dxy = df["DXY"].dropna()
    if len(dxy) < 50:
        return {}
    
    current = float(dxy.iloc[-1])
    ma_20 = float(dxy.tail(20).mean())
    ma_50 = float(dxy.tail(50).mean())
    
    if current > ma_20 > ma_50:
        trend = "up"
    elif current < ma_20 < ma_50:
        trend = "down"
    else:
        trend = "flat"
    
    return {
        "current": current,
        "ma_20": ma_20,
        "ma_50": ma_50,
        "trend": trend,
        "above_50ma": current > ma_50,
    }


def get_vix_signal() -> dict:
    """
    Get VIX regime signal for use as universal filter.
    
    Returns:
    {
        "current": float,
        "ma_20": float,
        "regime": str,  # "risk_off" / "elevated" / "risk_on" / "complacent"
    }
    """
    df = load_macro()
    if df.empty or "VIX" not in df.columns:
        return {}
    
    vix = df["VIX"].dropna()
    if len(vix) < 20:
        return {}
    
    current = float(vix.iloc[-1])
    ma_20 = float(vix.tail(20).mean())
    
    if current > 30:
        regime = "risk_off"
    elif current > 25:
        regime = "elevated"
    elif current < 13:
        regime = "complacent"
    else:
        regime = "risk_on"
    
    return {
        "current": current,
        "ma_20": ma_20,
        "regime": regime,
    }


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Fetch macro data (DXY, yields, VIX)")
    ap.add_argument("--force", action="store_true", help="Force refresh cache")
    args = ap.parse_args()
    
    df = load_macro(force=args.force)
    print(f"\nMacro Data — {len(df)} rows")
    print(f"Columns: {list(df.columns)}")
    print(f"\nLatest values:")
    for col in df.columns:
        val = df[col].iloc[-1]
        print(f"  {col}: {val:.4f}" if pd.notna(val) else f"  {col}: N/A")
    
    print(f"\n--- Yield Curve Signal ---")
    yc = get_yield_curve_signal()
    for k, v in yc.items():
        print(f"  {k}: {v}")
    
    print(f"\n--- DXY Signal ---")
    dxy = get_dxy_signal()
    for k, v in dxy.items():
        print(f"  {k}: {v}")
    
    print(f"\n--- VIX Signal ---")
    vix = get_vix_signal()
    for k, v in vix.items():
        print(f"  {k}: {v}")
