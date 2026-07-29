#!/usr/bin/env python3
"""
fetch_6h_data.py — HermesForge AdaptiveTrend Strategy

Fetches 6-hour OHLCV bars for the crypto universe from Hyperliquid's
public REST API. Hyperliquid does not natively support 6h candles, so
we fetch 2h candles and resample 3:1 into 6h bars.

For stocks, daily bars are already available via fetch_data.py (yfinance).
The scanner is timeframe-agnostic and works on any OHLCV DataFrame with
columns: open, high, low, close, volume, indexed by date/datetime.

Caches at ~/.hermes/market_data/6h/<SYMBOL>.parquet

Usage:
    python3 fetch_6h_data.py [--force]
"""

import sys
import time
import pathlib
import datetime
import requests
import pandas as pd
import numpy as np

# Import crypto universe from the existing fetcher
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from fetch_crypto_data import CRYPTO_UNIVERSE

CACHE_DIR = pathlib.Path.home() / ".hermes" / "market_data" / "6h"
HYPERLIQUID_INFO_URL = "https://api.hyperliquid.xyz/info"
CACHE_MAX_AGE_DAYS = 1  # crypto trades 24/7, refresh daily
START_DATE = "2020-01-01"


def cache_path(symbol: str) -> pathlib.Path:
    return CACHE_DIR / f"{symbol}.parquet"


def needs_refresh(symbol: str) -> bool:
    p = cache_path(symbol)
    if not p.exists():
        return True
    age = datetime.datetime.now() - datetime.datetime.fromtimestamp(p.stat().st_mtime)
    return age.days >= CACHE_MAX_AGE_DAYS


def _fetch_2h_candles(symbol: str, start_date: str = START_DATE) -> list:
    """Fetch 2h candles from Hyperliquid (native support)."""
    start_ms = int(pd.Timestamp(start_date).timestamp() * 1000)
    end_ms = int(datetime.datetime.utcnow().timestamp() * 1000)

    resp = requests.post(
        HYPERLIQUID_INFO_URL,
        json={"type": "candleSnapshot", "req": {"coin": symbol, "interval": "2h",
                                                   "startTime": start_ms, "endTime": end_ms}},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def _resample_2h_to_6h(candles_2h: list) -> pd.DataFrame:
    """Resample 2h candles into 6h bars (3:1). Groups by 6h windows."""
    if not candles_2h:
        return pd.DataFrame()

    rows = []
    for c in candles_2h:
        rows.append({
            "date": pd.to_datetime(c["t"], unit="ms"),
            "open": float(c["o"]),
            "high": float(c["h"]),
            "low": float(c["l"]),
            "close": float(c["c"]),
            "volume": float(c["v"]),
        })

    df = pd.DataFrame(rows).set_index("date").sort_index()

    # Resample to 6h: aggregate every 3 bars
    # OHLCV rules: open=first, high=max, low=min, close=last, volume=sum
    df_6h = df.resample("6h", label="left", closed="left").agg({
        "open": "first",
        "high": "max",
        "low": "min",
        "close": "last",
        "volume": "sum",
    }).dropna()

    return df_6h


def fetch_symbol(symbol: str, start_date: str = START_DATE) -> pd.DataFrame:
    """Fetch 6h candles for a Hyperliquid symbol via 2h resample."""
    candles = _fetch_2h_candles(symbol, start_date)
    if not candles:
        return pd.DataFrame()
    return _resample_2h_to_6h(candles)


def fetch_all(force: bool = False) -> dict:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    results = {}
    for symbol in CRYPTO_UNIVERSE:
        if not force and not needs_refresh(symbol):
            results[symbol] = "cached"
            continue
        print(f"Fetching 6h data for {symbol}...")
        try:
            df = fetch_symbol(symbol)
            if df.empty:
                results[symbol] = "no_data"
                continue
            df["ticker"] = symbol
            df["subperiod"] = "crypto_unlabeled"
            df.to_parquet(cache_path(symbol))
            results[symbol] = f"ok ({len(df)} bars, {df.index[0].date()} to {df.index[-1].date()})"
        except Exception as e:
            results[symbol] = f"error: {e}"
        time.sleep(0.3)  # polite rate limit
    return results


def load_symbol(symbol: str) -> pd.DataFrame:
    p = cache_path(symbol)
    if not p.exists():
        raise FileNotFoundError(f"No cached 6h data for {symbol}. Run fetch_all() first.")
    return pd.read_parquet(p)


def load_all() -> dict:
    """Load all cached 6h crypto data."""
    result = {}
    for symbol in CRYPTO_UNIVERSE:
        try:
            result[symbol] = load_symbol(symbol)
        except FileNotFoundError:
            continue
    return result


if __name__ == "__main__":
    force = "--force" in sys.argv
    results = fetch_all(force=force)
    print("\n=== 6h Fetch Results ===")
    for symbol, status in results.items():
        print(f"  {symbol}: {status}")
