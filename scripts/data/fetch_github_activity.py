#!/usr/bin/env python3
"""
fetch_github_activity.py — GitHub commit activity for major crypto projects

Tracks developer engagement as a fundamental signal. Uses the GitHub stats API
endpoint /repos/{owner}/{repo}/stats/commit_activity which returns weekly commit
counts for the last year (52 weeks).

Free API, no key required (60 req/hr unauthenticated, 5000/hr with key).
Set GITHUB_TOKEN env var to use authenticated rate limit.

Caches to ~/.hermes/market_data/github/commit_activity.parquet
Refreshes if cache > 12 hours old.

Usage:
    python3 fetch_github_activity.py              # fetch/update
    python3 fetch_github_activity.py --force       # force refresh
    python3 fetch_github_activity.py --summary     # print regime summary
"""

import os
import sys
import time
import json
import pathlib
import argparse
import requests
import pandas as pd
from datetime import datetime, timezone

API_BASE = "https://api.github.com/repos/{owner}/{repo}/stats/commit_activity"
CACHE_PATH = pathlib.Path.home() / ".hermes" / "market_data" / "github" / "commit_activity.parquet"
CACHE_MAX_AGE_HOURS = 12

# Coin -> (owner, repo) mapping
COIN_REPOS = {
    "BTC":  ("bitcoin",            "bitcoin"),
    "ETH":  ("ethereum",           "go-ethereum"),
    "SOL":  ("solana-labs",        "solana"),
    "AVAX": ("ava-labs",           "avalanchego"),
    "LINK": ("smartcontractkit",   "chainlink"),
    "DOGE": ("dogecoin",           "dogecoin"),
    "ARB":  ("offchainlabs",       "nitro"),
    "OP":   ("ethereum-optimism",  "optimism"),
    "SUI":  ("MystenLabs",         "sui"),
    "BNB":  ("bnb-chain",          "bsc"),
}

# Threshold for trend classification (relative change between first and second
# half of the 8-week lookback window).
TREND_THRESHOLD = 0.08  # 8% relative change => up/down, else flat


def _auth_headers() -> dict:
    """Return request headers with optional GitHub token auth."""
    headers = {"Accept": "application/vnd.github+json"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _repo_url(coin: str) -> str:
    owner, repo = COIN_REPOS[coin]
    return f"https://github.com/{owner}/{repo}"


def fetch_repo_activity(coin: str, max_retries: int = 3) -> list:
    """
    Fetch weekly commit activity for a coin's repo.

    The stats endpoint may return 202 (generating stats) on first call;
    we retry after a short sleep until we get 200.

    Returns:
        List of weekly dicts: [{"week": <unix_ts>, "total": <int>, "days": [...]}, ...]
    """
    owner, repo = COIN_REPOS[coin]
    url = API_BASE.format(owner=owner, repo=repo)
    headers = _auth_headers()

    for attempt in range(max_retries):
        resp = requests.get(url, headers=headers, timeout=30)
        if resp.status_code == 202:
            # GitHub is generating statistics; wait and retry
            time.sleep(5)
            continue
        if resp.status_code == 404:
            print(f"[WARN] {coin}: repo not found ({owner}/{repo})", file=sys.stderr)
            return []
        if resp.status_code == 403:
            # Rate limit hit
            reset = resp.headers.get("X-RateLimit-Reset")
            msg = f"GitHub rate limit exceeded for {coin}"
            if reset:
                reset_dt = datetime.fromtimestamp(int(reset), tz=timezone.utc)
                msg += f". Resets at {reset_dt.isoformat()}"
            print(f"[WARN] {msg}", file=sys.stderr)
            return []
        resp.raise_for_status()
        return resp.json()

    print(f"[WARN] {coin}: stats not ready after {max_retries} retries", file=sys.stderr)
    return []


def fetch_github_activity(coins: list | None = None) -> pd.DataFrame:
    """
    Fetch commit activity for all (or specified) coins.

    Returns:
        DataFrame with columns: coin, week (Timestamp), total_commits (int)
    """
    if coins is None:
        coins = list(COIN_REPOS.keys())

    rows = []
    for coin in coins:
        if coin not in COIN_REPOS:
            print(f"[WARN] Unknown coin {coin}, skipping", file=sys.stderr)
            continue
        activity = fetch_repo_activity(coin)
        if not activity:
            continue
        for week_data in activity:
            week_ts = week_data.get("week")
            total = week_data.get("total", 0)
            if week_ts is None:
                continue
            rows.append({
                "coin": coin,
                "week": pd.Timestamp(datetime.fromtimestamp(week_ts, tz=timezone.utc).strftime("%Y-%m-%d")),
                "total_commits": int(total),
            })
        print(f"  {coin}: {len(activity)} weeks fetched", file=sys.stderr)
        # Be polite to the API between repos
        time.sleep(1)

    if not rows:
        return pd.DataFrame(columns=["coin", "week", "total_commits"])

    df = pd.DataFrame(rows).sort_values(["coin", "week"]).reset_index(drop=True)
    return df


def load_github_activity(force: bool = False, coins: list | None = None) -> pd.DataFrame:
    """
    Load GitHub activity data from cache or fetch fresh.
    """
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)

    if not force and CACHE_PATH.exists():
        mtime = datetime.fromtimestamp(CACHE_PATH.stat().st_mtime, tz=timezone.utc)
        age = (datetime.now(timezone.utc) - mtime).total_seconds() / 3600
        if age < CACHE_MAX_AGE_HOURS:
            return pd.read_parquet(CACHE_PATH)

    df = fetch_github_activity(coins=coins)
    if not df.empty:
        df.to_parquet(CACHE_PATH, index=False)
        print(f"GitHub activity: {len(df)} weeks cached to {CACHE_PATH}", file=sys.stderr)
    else:
        # If fetch fails but we have stale cache, fall back to it
        if CACHE_PATH.exists():
            print("[WARN] Fetch returned no data; using stale cache", file=sys.stderr)
            return pd.read_parquet(CACHE_PATH)
    return df


def _classify_trend(recent8: list) -> str:
    """
    Classify trend from the last 8 weeks of commits.

    Compares the first 4 weeks to the last 4 weeks. If the relative change
    exceeds TREND_THRESHOLD, returns 'up' or 'down', otherwise 'flat'.
    """
    if len(recent8) < 4:
        return "flat"
    first_half = recent8[: len(recent8) // 2]
    second_half = recent8[len(recent8) // 2 :]
    avg_first = sum(first_half) / len(first_half) if first_half else 0
    avg_second = sum(second_half) / len(second_half) if second_half else 0
    if avg_first == 0:
        return "up" if avg_second > 0 else "flat"
    rel_change = (avg_second - avg_first) / avg_first
    if rel_change > TREND_THRESHOLD:
        return "up"
    if rel_change < -TREND_THRESHOLD:
        return "down"
    return "flat"


def get_github_summary(force: bool = False) -> dict:
    """
    Return a summary dict suitable for the regime filter.

    Returns:
        {coin: {avg_commits_4w, trend, repo_url}}
    """
    df = load_github_activity(force=force)
    summary = {}
    if df.empty:
        return summary

    for coin in COIN_REPOS:
        coin_df = df[df["coin"] == coin].sort_values("week")
        if coin_df.empty:
            continue
        recent4 = coin_df.tail(4)["total_commits"].tolist()
        recent8 = coin_df.tail(8)["total_commits"].tolist()
        avg_4w = sum(recent4) / len(recent4) if recent4 else 0.0
        trend = _classify_trend(recent8)
        summary[coin] = {
            "avg_commits_4w": round(avg_4w, 1),
            "trend": trend,
            "repo_url": _repo_url(coin),
        }
    return summary


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Fetch GitHub commit activity for crypto projects")
    ap.add_argument("--force", action="store_true", help="Force refresh cache")
    ap.add_argument("--summary", action="store_true", help="Print regime-filter summary")
    ap.add_argument("--coins", type=str, default="", help="Comma-separated coins (default: all)")
    args = ap.parse_args()

    coins = [c.strip().upper() for c in args.coins.split(",") if c.strip()] or None

    df = load_github_activity(force=args.force, coins=coins)
    print(f"\nGitHub Commit Activity — {len(df)} week-coin records")
    if not df.empty:
        print(f"Coins: {sorted(df['coin'].unique())}")
        print(f"Date range: {df['week'].min().date()} → {df['week'].max().date()}")

    if args.summary or df.empty:
        summary = get_github_summary(force=args.force)
        print("\nGitHub Regime Summary:")
        print(f"{'Coin':<6} {'AvgCommits4w':>14}  {'Trend':<6}  Repo")
        print("-" * 70)
        for coin, info in sorted(summary.items()):
            print(f"{coin:<6} {info['avg_commits_4w']:>14.1f}  {info['trend']:<6}  {info['repo_url']}")
