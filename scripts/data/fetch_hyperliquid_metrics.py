#!/usr/bin/env python3
"""
fetch_hyperliquid_metrics.py — Funding Rates + Open Interest from Hyperliquid

Uses the same free public API as fetch_crypto_data.py (no auth needed).
Funding rates show market positioning sentiment. Open interest shows
capital committed to the market.

Caches to ~/.hermes/market_data/hyperliquid_metrics/

Usage:
    python3 fetch_hyperliquid_metrics.py              # fetch latest
    python3 fetch_hyperliquid_metrics.py --force      # force refresh
    python3 fetch_hyperliquid_metrics.py --coin BTC   # single coin
"""

import sys
import time
import json
import pathlib
import argparse
import requests
import pandas as pd
from datetime import datetime, timezone, timedelta

HYPERLIQUID_INFO_URL = "https://api.hyperliquid.xyz/info"
CACHE_DIR = pathlib.Path.home() / ".hermes" / "market_data" / "hyperliquid_metrics"
CACHE_MAX_AGE_HOURS = 6  # Funding updates hourly, refresh every 6h

# Same universe as fetch_crypto_data.py
CRYPTO_UNIVERSE = [
    "BTC", "ETH", "SOL", "AVAX", "LINK", "DOGE", "ARB", "OP", "SUI", "BNB",
]


def fetch_funding_history(coin: str, hours: int = 168) -> pd.DataFrame:
    """
    Fetch funding rate history for a coin.
    Default: last 7 days (168 hours).
    
    Returns DataFrame: timestamp, funding_rate, premium
    """
    end_time = int(time.time() * 1000)
    start_time = int((time.time() - hours * 3600) * 1000)
    
    resp = requests.post(
        HYPERLIQUID_INFO_URL,
        json={"type": "fundingHistory", "coin": coin,
              "startTime": start_time, "endTime": end_time},
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    
    if not data:
        return pd.DataFrame(columns=["timestamp", "funding_rate", "premium"])
    
    df = pd.DataFrame(data)
    df["timestamp"] = pd.to_datetime(df["time"], unit="ms", utc=True)
    df["funding_rate"] = df["fundingRate"].astype(float)
    if "premium" in df.columns:
        df["premium"] = df["premium"].astype(float)
    df["coin"] = coin
    return df[["timestamp", "coin", "funding_rate", "premium"]]


def fetch_open_interest() -> dict:
    """
    Fetch current open interest for all coins via meta endpoint.
    Returns {coin: {"open_interest": float, "max_leverage": int}}
    """
    resp = requests.post(
        HYPERLIQUID_INFO_URL,
        json={"type": "meta"},
        timeout=30,
    )
    resp.raise_for_status()
    universe = resp.json().get("universe", [])
    
    # Get asset contexts for OI values
    resp2 = requests.post(
        HYPERLIQUID_INFO_URL,
        json={"type": "metaAndAssetCtxs"},
        timeout=30,
    )
    resp2.raise_for_status()
    result_meta = resp2.json()
    
    # metaAndAssetCtxs returns [universe_meta, asset_contexts]
    if isinstance(result_meta, list) and len(result_meta) == 2:
        universe = result_meta[0].get("universe", result_meta[0])
        ctxs = result_meta[1]
    else:
        universe = result_meta.get("universe", [])
        ctxs = []
    
    result = {}
    for i, asset in enumerate(universe):
        if asset.get("isDelisted"):
            continue
        name = asset["name"]
        ctx = ctxs[i] if i < len(ctxs) else {}
        result[name] = {
            "open_interest": float(ctx.get("openInterest", 0) or 0),
            "max_leverage": int(asset.get("maxLeverage", 1)),
            "funding_rate": float(ctx.get("funding", 0) or 0),
            "prev_funding_rate": float(ctx.get("prevDayFunding", 0) or 0),
            "oracle_price": float(ctx.get("oraclePrice", 0) or 0),
            "mark_price": float(ctx.get("markPrice", 0) or 0),
        }
    
    return result


def load_funding_history(coin: str, hours: int = 168, force: bool = False) -> pd.DataFrame:
    """Load funding history from cache or fetch fresh."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_path = CACHE_DIR / f"funding_{coin}.parquet"
    
    if not force and cache_path.exists():
        mtime = datetime.fromtimestamp(cache_path.stat().st_mtime, tz=timezone.utc)
        age = (datetime.now(timezone.utc) - mtime).total_seconds() / 3600
        if age < CACHE_MAX_AGE_HOURS:
            return pd.read_parquet(cache_path)
    
    df = fetch_funding_history(coin, hours)
    df.to_parquet(cache_path, index=False)
    return df


def load_all_metrics(coins: list = None, force: bool = False) -> dict:
    """
    Load funding history + current OI for all coins.
    
    Returns:
    {
        "funding": {coin: DataFrame},
        "open_interest": {coin: dict},
        "timestamp": ISO string,
    }
    """
    if coins is None:
        coins = CRYPTO_UNIVERSE
    
    funding = {}
    for coin in coins:
        try:
            df = load_funding_history(coin, force=force)
            funding[coin] = df
        except Exception as e:
            print(f"  Warning: {coin} funding fetch failed: {e}", file=sys.stderr)
            funding[coin] = pd.DataFrame()
    
    oi = {}
    try:
        oi = fetch_open_interest()
    except Exception as e:
        print(f"  Warning: OI fetch failed: {e}", file=sys.stderr)
    
    return {
        "funding": funding,
        "open_interest": oi,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def get_funding_summary(coins: list = None) -> dict:
    """
    Get current funding rate summary for signal generation.
    
    Returns:
    {
        coin: {
            "current_rate": float,      # latest funding rate
            "avg_7d": float,            # 7-day average
            "extreme": str,             # "positive_extreme" / "negative_extreme" / "neutral"
            "open_interest": float,    # current OI in USD
        }
    }
    """
    if coins is None:
        coins = CRYPTO_UNIVERSE
    
    metrics = load_all_metrics(coins)
    oi_data = metrics["open_interest"]
    
    summary = {}
    for coin in coins:
        df = metrics["funding"].get(coin, pd.DataFrame())
        if df.empty:
            continue
        
        current = float(df.iloc[-1]["funding_rate"])
        avg_7d = float(df["funding_rate"].mean())
        
        # Extreme thresholds (Hyperliquid funding is per-8h, ~0.0125% = neutral)
        # Extreme positive: > 0.05% per 8h = crowded long
        # Extreme negative: < -0.02% per 8h = crowded short
        if current > 0.0005:
            extreme = "positive_extreme"
        elif current < -0.0002:
            extreme = "negative_extreme"
        else:
            extreme = "neutral"
        
        oi = oi_data.get(coin, {}).get("open_interest", 0)
        # OI is in coin units, convert to USD using mark price
        mark = oi_data.get(coin, {}).get("mark_price", 0)
        oi_usd = oi * mark if mark else 0
        
        summary[coin] = {
            "current_rate": current,
            "avg_7d": avg_7d,
            "extreme": extreme,
            "open_interest": oi,
            "open_interest_usd": oi_usd,
        }
    
    return summary


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Fetch Hyperliquid funding + OI metrics")
    ap.add_argument("--force", action="store_true", help="Force refresh cache")
    ap.add_argument("--coin", type=str, default=None, help="Single coin")
    args = ap.parse_args()
    
    coins = [args.coin] if args.coin else CRYPTO_UNIVERSE
    
    summary = get_funding_summary(coins)
    print("\nHyperliquid Funding Rate + Open Interest Summary")
    print("=" * 70)
    print(f"{'Coin':<8} {'Funding %':<12} {'7d Avg %':<12} {'Signal':<20} {'OI ($)':<15}")
    print("-" * 70)
    
    for coin, data in summary.items():
        fr = data["current_rate"] * 100  # to percentage
        avg = data["avg_7d"] * 100
        oi = data["open_interest"]
        print(f"{coin:<8} {fr:+.4f}%     {avg:+.4f}%     {data['extreme']:<20} ${oi:>12,.0f}")
