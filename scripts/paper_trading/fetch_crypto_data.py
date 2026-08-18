#!/usr/bin/env python3
"""
fetch_crypto_data.py — HermesForge EPIC-010 (US-069)

Fetches daily OHLCV for the approved crypto paper-trading universe
(BTC, ETH, SOL) from Hyperliquid's public market-data REST endpoint
(no auth required). Caches in the same column schema as stock parquet
files for scanner compatibility.

DECISION (resolved during implementation, 2026-07-20): Hyperliquid's
public candleSnapshot endpoint provides sufficient history (980+ daily
bars for BTC back to 2020-08-19, similar depth for ETH/SOL) -- no need
for a yfinance crypto fallback. This also directly reuses the same data
source planned for EPIC-011 (Hyperliquid testnet), avoiding a second
crypto data vendor.

Usage:
    python3 fetch_crypto_data.py [--force]
"""

import sys
import time
import pathlib
import datetime
import requests
import pandas as pd

CACHE_DIR = pathlib.Path.home() / ".hermes" / "market_data" / "crypto"
HYPERLIQUID_INFO_URL = "https://api.hyperliquid.xyz/info"
# --- Universe (single source of truth) ----------------------------------------
import pathlib as _pl
import sys as _sys
_sys.path.insert(0, str(_pl.Path(__file__).resolve().parent.parent))
from config.universe import CRYPTO_UNIVERSE  # noqa: E402
CACHE_MAX_AGE_DAYS = 1  # crypto trades 24/7, refresh more often than stocks


def cache_path(symbol: str) -> pathlib.Path:
    return CACHE_DIR / f"{symbol}.parquet"


def needs_refresh(symbol: str) -> bool:
    p = cache_path(symbol)
    if not p.exists():
        return True
    age = datetime.datetime.now() - datetime.datetime.fromtimestamp(p.stat().st_mtime)
    return age.days >= CACHE_MAX_AGE_DAYS


def fetch_symbol(symbol: str, start_date: str = "2019-01-01") -> pd.DataFrame:
    """Fetch daily candles for a Hyperliquid coin symbol, returns scanner-compatible DataFrame."""
    start_ms = int(pd.Timestamp(start_date).timestamp() * 1000)
    end_ms = int(datetime.datetime.utcnow().timestamp() * 1000)

    resp = requests.post(
        HYPERLIQUID_INFO_URL,
        json={"type": "candleSnapshot", "req": {"coin": symbol, "interval": "1d",
                                                   "startTime": start_ms, "endTime": end_ms}},
        timeout=30,
    )
    resp.raise_for_status()
    candles = resp.json()

    if not candles:
        return pd.DataFrame()

    rows = []
    for c in candles:
        rows.append({
            "date": pd.to_datetime(c["t"], unit="ms"),
            "open": float(c["o"]),
            "high": float(c["h"]),
            "low": float(c["l"]),
            "close": float(c["c"]),
            "volume": float(c["v"]),
        })

    df = pd.DataFrame(rows).set_index("date").sort_index()
    df["ticker"] = symbol
    # Crypto trades 24/7 -- no bull/bear/current sub-period labeling applied here yet
    # (see US-076 for crypto strategy adaptation / weekly-bar-definition decision)
    df["subperiod"] = "crypto_unlabeled"
    return df


def fetch_all(force: bool = False) -> dict:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    results = {}
    for symbol in CRYPTO_UNIVERSE:
        if not force and not needs_refresh(symbol):
            results[symbol] = "cached"
            continue
        print(f"Fetching {symbol}...")
        try:
            df = fetch_symbol(symbol)
            if df.empty:
                results[symbol] = "no_data"
                continue
            df.to_parquet(cache_path(symbol))
            results[symbol] = f"ok ({len(df)} bars, {df.index[0].date()} to {df.index[-1].date()})"
        except Exception as e:
            results[symbol] = f"error: {e}"
        time.sleep(0.3)  # polite rate limit
    return results


def load_symbol(symbol: str) -> pd.DataFrame:
    p = cache_path(symbol)
    if not p.exists():
        raise FileNotFoundError(f"No cached crypto data for {symbol}. Run fetch_all() first.")
    return pd.read_parquet(p)


def load_all() -> dict:
    """Load all cached crypto data. Filters out stale tickers (last bar > 14 days old)
    to prevent delisted coins from polluting cross-sectional scanners."""
    import pandas as pd
    result = {}
    staleness_cutoff = pd.Timestamp.now(tz=None) - pd.Timedelta(days=14)
    skipped = []
    for symbol in CRYPTO_UNIVERSE:
        try:
            df = load_symbol(symbol)
            if df.index[-1] < staleness_cutoff:
                skipped.append((symbol, str(df.index[-1])[:10]))
                continue
            result[symbol] = df
        except FileNotFoundError:
            continue
    if skipped:
        print(f"  [load_all] Skipped {len(skipped)} stale ticker(s): "
              + ", ".join(f"{t} ({d})" for t, d in skipped))
    return result


if __name__ == "__main__":
    force = "--force" in sys.argv
    results = fetch_all(force=force)
    print("\n=== Fetch Results ===")
    for symbol, status in results.items():
        print(f"  {symbol}: {status}")
