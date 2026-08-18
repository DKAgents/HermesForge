#!/usr/bin/env python3
"""
fetch_lunarcrush.py — LunarCrush Social Sentiment Data

Free tier: per-coin and per-stock snapshots (no batch lists, no time-series).
We collect daily snapshots to build our own historical dataset over time.

Available on free:
  - /coins/:coin/v1 — Galaxy Score, price, volume, volatility, market cap
  - /stocks/:stock/v1 — price, volume, market cap
  - /topic/:topic/v1 — post counts, interactions, sentiment per platform, trend
  - /categories/list/v1 — all 40 categories

Not on free (need Individual $5/day):
  - /coins/list/v2 — batch coin list
  - /coins/:coin/time-series/v2 — historical time-series
  - /topics/list/v1 — batch topic list
  - AltRank, num_contributors, num_posts, interactions_24h

Strategy: Fetch daily snapshots for our crypto + stock universe.
Cache each day's snapshot to build historical data over time.

Usage:
    python3 fetch_lunarcrush.py                    # fetch crypto + stocks
    python3 fetch_lunarcrush.py --crypto-only      # crypto only
    python3 fetch_lunarcrush.py --stocks-only      # stocks only
    python3 fetch_lunarcrush.py --topics           # topic sentiment only
"""

import sys
import os
import time
import json
import pathlib
import argparse
import requests
import pandas as pd
from datetime import datetime, timezone

BASE_URL = "https://lunarcrush.com/api4/public"
CACHE_DIR = pathlib.Path.home() / ".hermes" / "market_data" / "lunarcrush"
CACHE_MAX_AGE_HOURS = 12

# Crypto universe (same as fetch_crypto_data.py)
# --- Universe (single source of truth) ----------------------------------------
import pathlib as _pl
import sys as _sys
_sys.path.insert(0, str(_pl.Path(__file__).resolve().parent.parent))
from config.universe import CRYPTO_UNIVERSE  # noqa: E402

# Stock universe — fetch subset for efficiency (top 50 by liquidity)
# Full 529 would use too many API calls on free tier
STOCK_UNIVERSE = [
    "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA", "AVGO", "AMD",
    "JPM", "BAC", "GS", "V", "JNJ", "UNH", "WMT", "PG", "MA", "HD", "COST",
    "NFLX", "CRM", "ADBE", "INTC", "MU", "AMAT", "LRCX", "PANW", "CRWD", "SNOW",
    "XOM", "CVX", "CAT", "BA", "RTX", "LMT", "DIS", "PYPL", "UBER", "SHOP",
    "PLTR", "SNPS", "TTWO", "SPOT", "BKNG", "ABNB", "ALLE", "AXON", "ROST", "AMCR",
]

# Topics to track (our 7 selected categories + key assets)
# Topic slugs must match LunarCrush's internal naming
TOPICS = [
    "bitcoin", "ethereum", "cryptocurrency", "solana",
    "finance", "stocks", "technology",
]


def _get_api_key() -> str:
    """Load API key from .env file."""
    env_path = pathlib.Path.home() / ".hermes" / ".env"
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                if line.startswith("LUNARCRUSH_API_KEY="):
                    return line.strip().split("=", 1)[1]
    # Fallback to env var
    return os.environ.get("LUNARCRUSH_API_KEY", "")


def _api_get(endpoint: str, params: dict = None) -> dict:
    """Make an authenticated GET request to LunarCrush API."""
    api_key = _get_api_key()
    if not api_key:
        raise ValueError("LUNARCRUSH_API_KEY not set in ~/.hermes/.env")
    
    url = f"{BASE_URL}/{endpoint}"
    headers = {"Authorization": f"Bearer {api_key}"}
    
    resp = requests.get(url, headers=headers, params=params, timeout=20)
    resp.raise_for_status()
    return resp.json()


def _coin_to_topic(coin: str) -> str:
    """Convert coin symbol to LunarCrush topic slug."""
    TOPIC_MAP = {
        "BTC": "bitcoin", "ETH": "ethereum", "SOL": "solana",
        "AVAX": "avalanche", "LINK": "chainlink", "DOGE": "dogecoin",
        "ARB": "arbitrum", "OP": "optimism", "SUI": "sui", "BNB": "bnb",
    }
    return TOPIC_MAP.get(coin.upper(), coin.lower())


COIN_TO_ID = {
    "BTC": "bitcoin", "ETH": "ethereum", "SOL": "solana",
    "AVAX": "avalanche", "LINK": "chainlink", "DOGE": "dogecoin",
    "ARB": "arbitrum", "OP": "optimism", "SUI": "sui", "BNB": "bnb",
}


def fetch_coin_data(coin: str) -> dict:
    """Fetch current data for a single cryptocurrency."""
    coin_id = COIN_TO_ID.get(coin.upper(), coin.lower())
    try:
        resp = _api_get(f"coins/{coin_id}/v1")
        data = resp.get("data", {})
        return {
            "symbol": coin.upper(),
            "galaxy_score": data.get("galaxy_score"),
            "alt_rank": data.get("alt_rank"),
            "price": data.get("price"),
            "percent_change_24h": data.get("percent_change_24h"),
            "percent_change_7d": data.get("percent_change_7d"),
            "volume_24h": data.get("volume_24h"),
            "market_cap": data.get("market_cap"),
            "volatility": data.get("volatility"),
            "market_cap_rank": data.get("market_cap_rank"),
        }
    except Exception as e:
        return {"symbol": coin.upper(), "error": str(e)}


def fetch_stock_data(symbol: str) -> dict:
    """Fetch current social+market data for a single stock."""
    try:
        resp = _api_get(f"stocks/{symbol}/v1")
        data = resp.get("data", {})
        return {
            "symbol": symbol,
            "price": data.get("price"),
            "percent_change_24h": data.get("percent_change_24h"),
            "volume_24h": data.get("volume_24h"),
            "market_cap": data.get("market_cap"),
            "market_cap_rank": data.get("market_cap_rank"),
        }
    except Exception as e:
        return {"symbol": symbol, "error": str(e)}


def fetch_topic_data(topic: str) -> dict:
    """Fetch social sentiment data for a topic."""
    try:
        resp = _api_get(f"topic/{topic}/v1")
        data = resp.get("data", {})
        
        # Extract sentiment detail
        sentiment_detail = data.get("types_sentiment_detail", {})
        tweet_sent = sentiment_detail.get("tweet", {})
        
        # Aggregate sentiment across all platforms
        all_sentiments = data.get("types_sentiment", {})
        avg_sentiment = sum(all_sentiments.values()) / len(all_sentiments) if all_sentiments else 50
        
        # Total post count and interactions
        types_count = data.get("types_count", {})
        total_posts = sum(types_count.values()) if types_count else 0
        
        types_interactions = data.get("types_interactions", {})
        total_interactions = sum(types_interactions.values()) if types_interactions else 0
        
        return {
            "topic": topic,
            "topic_rank": data.get("topic_rank"),
            "trend": data.get("trend"),
            "total_posts": total_posts,
            "total_interactions": total_interactions,
            "avg_sentiment": round(avg_sentiment, 1),
            "tweet_sentiment": all_sentiments.get("tweet", 50),
            "reddit_sentiment": all_sentiments.get("reddit-post", 50),
            "news_sentiment": all_sentiments.get("news", 50),
            "tweet_count": types_count.get("tweet", 0),
            "reddit_count": types_count.get("reddit-post", 0),
            "news_count": types_count.get("news", 0),
        }
    except Exception as e:
        return {"topic": topic, "error": str(e)}


def collect_crypto_snapshot(coins: list = None) -> pd.DataFrame:
    """
    Fetch Galaxy Score + market data for all coins.
    Returns DataFrame with one row per coin.
    """
    if coins is None:
        coins = CRYPTO_UNIVERSE
    
    rows = []
    for i, coin in enumerate(coins):
        data = fetch_coin_data(coin)
        data["timestamp"] = datetime.now(timezone.utc).isoformat()
        rows.append(data)
        if (i + 1) % 5 == 0:
            print(f"  Fetched {i+1}/{len(coins)} coins...", file=sys.stderr)
        time.sleep(0.3)  # be gentle on rate limits
    
    df = pd.DataFrame(rows)
    # Extract galaxy_score for easy access
    df["galaxy_score"] = pd.to_numeric(df.get("galaxy_score"), errors="coerce")
    return df


def collect_stock_snapshot(symbols: list = None) -> pd.DataFrame:
    """Fetch social+market data for stocks."""
    if symbols is None:
        symbols = STOCK_UNIVERSE
    
    rows = []
    for i, sym in enumerate(symbols):
        data = fetch_stock_data(sym)
        data["timestamp"] = datetime.now(timezone.utc).isoformat()
        rows.append(data)
        if (i + 1) % 10 == 0:
            print(f"  Fetched {i+1}/{len(symbols)} stocks...", file=sys.stderr)
        time.sleep(0.3)
    
    return pd.DataFrame(rows)


def collect_topic_snapshot(topics: list = None) -> pd.DataFrame:
    """Fetch topic sentiment data."""
    if topics is None:
        topics = TOPICS
    
    rows = []
    for i, topic in enumerate(topics):
        data = fetch_topic_data(topic)
        data["timestamp"] = datetime.now(timezone.utc).isoformat()
        rows.append(data)
        if (i + 1) % 5 == 0:
            print(f"  Fetched {i+1}/{len(topics)} topics...", file=sys.stderr)
        time.sleep(0.3)
    
    return pd.DataFrame(rows)


def save_daily_snapshot(df: pd.DataFrame, data_type: str) -> pathlib.Path:
    """
    Save today's snapshot to dated parquet file.
    Builds historical dataset over time.
    """
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    path = CACHE_DIR / f"{data_type}_{today}.parquet"
    df.to_parquet(path, index=False)
    return path


def load_latest_crypto_snapshot() -> pd.DataFrame:
    """Load the most recent crypto snapshot."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    files = sorted(CACHE_DIR.glob("crypto_*.parquet"), reverse=True)
    if not files:
        return pd.DataFrame()
    return pd.read_parquet(files[0])


def load_latest_topics_snapshot() -> pd.DataFrame:
    """Load the most recent topics snapshot."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    files = sorted(CACHE_DIR.glob("topics_*.parquet"), reverse=True)
    if not files:
        return pd.DataFrame()
    return pd.read_parquet(files[0])


def get_crypto_sentiment_summary(coins: list = None) -> dict:
    """
    Get current crypto sentiment summary for regime filter integration.
    
    Returns:
    {
        coin: {
            "galaxy_score": float,      # 0-100, higher = stronger social engagement
            "sentiment": float,         # 0-100, higher = more positive
            "trend": str,               # flat / bullish / bearish
            "volatility": float,        # from LunarCrush
        }
    }
    """
    if coins is None:
        coins = CRYPTO_UNIVERSE
    
    # Get coin data
    coin_df = collect_crypto_snapshot(coins)
    
    # Get topic data for each coin
    summary = {}
    for _, row in coin_df.iterrows():
        symbol = row.get("symbol", "")
        if not symbol or "error" in str(row.get("galaxy_score", "")):
            continue
        
        # Also fetch topic data for this coin
        topic = _coin_to_topic(symbol)
        topic_data = fetch_topic_data(topic)
        time.sleep(0.3)
        
        summary[symbol] = {
            "galaxy_score": float(row.get("galaxy_score", 50) or 50),
            "sentiment": topic_data.get("avg_sentiment", 50),
            "trend": topic_data.get("trend", "flat"),
            "total_posts": topic_data.get("total_posts", 0),
            "volatility": float(row.get("volatility", 0) or 0),
        }
    
    return summary


def get_topic_sentiment_summary(topics: list = None) -> dict:
    """
    Get topic sentiment for regime filter.
    
    Returns:
    {
        topic: {
            "sentiment": float,    # 0-100, higher = more positive
            "trend": str,          # flat / bullish / bearish
            "total_posts": int,
            "topic_rank": int,
        }
    }
    """
    if topics is None:
        topics = TOPICS
    
    topic_df = collect_topic_snapshot(topics)
    
    summary = {}
    for _, row in topic_df.iterrows():
        topic = row.get("topic", "")
        if not topic or "error" in str(row.get("avg_sentiment", "")):
            continue
        summary[topic] = {
            "sentiment": float(row.get("avg_sentiment", 50) or 50),
            "trend": row.get("trend", "flat"),
            "total_posts": int(row.get("total_posts", 0) or 0),
            "topic_rank": int(row.get("topic_rank", 0) or 0),
        }
    
    return summary


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Fetch LunarCrush social sentiment data")
    ap.add_argument("--crypto-only", action="store_true")
    ap.add_argument("--stocks-only", action="store_true")
    ap.add_argument("--topics-only", action="store_true")
    args = ap.parse_args()
    
    fetch_all = not (args.crypto_only or args.stocks_only or args.topics_only)
    
    if fetch_all or args.crypto_only:
        print("\n=== Crypto Coin Data ===")
        crypto_df = collect_crypto_snapshot()
        path = save_daily_snapshot(crypto_df, "crypto")
        print(f"Saved {len(crypto_df)} coins to {path}")
        print(f"  Galaxy Scores: {dict(zip(crypto_df['symbol'], crypto_df['galaxy_score']))}")
    
    if fetch_all or args.stocks_only:
        print("\n=== Stock Data ===")
        stock_df = collect_stock_snapshot()
        path = save_daily_snapshot(stock_df, "stocks")
        print(f"Saved {len(stock_df)} stocks to {path}")
    
    if fetch_all or args.topics_only:
        print("\n=== Topic Sentiment ===")
        topic_df = collect_topic_snapshot()
        path = save_daily_snapshot(topic_df, "topics")
        print(f"Saved {len(topic_df)} topics to {path}")
        for _, row in topic_df.iterrows():
            print(f"  {row.get('topic','?')}: sentiment={row.get('avg_sentiment','?')}, "
                  f"trend={row.get('trend','?')}, posts={row.get('total_posts','?')}")
