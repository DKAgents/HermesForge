#!/usr/bin/env python3
"""
fetch_reddit_sentiment.py — Reddit post volume & sentiment feed

Uses Reddit's free JSON API (no auth, just a descriptive User-Agent).
Fetches hot posts from r/CryptoCurrency, r/wallstreetbets, r/stocks,
r/StockMarket, counts ticker mentions from our stock + crypto universe,
and scores sentiment via simple bullish/bearish word counting.

Caches daily snapshots to ~/.hermes/market_data/reddit/<YYYY-MM-DD>.parquet
so historical sentiment builds up over time. A latest pointer
(latest.parquet) always mirrors the most recent fetch for quick reads.

Usage:
    python3 fetch_reddit_sentiment.py                # fetch + cache + summary
    python3 fetch_reddit_sentiment.py --force        # refetch ignoring cache age
    python3 fetch_reddit_sentiment.py --summary      # just print cached summary
"""

import sys
import re
import time
import pathlib
import argparse
import requests
import pandas as pd
from datetime import datetime, timezone

# --- Universe ---------------------------------------------------------------
# Import the stock UNIVERSE from the validation module (same pattern as
# run_phase1a.py — add the validation dir to sys.path).
REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "validation"))
from universe import get_universe as get_stock_universe  # noqa: E402

# Crypto universe (matches fetch_lunarcrush.py / fetch_crypto_data.py)
CRYPTO_UNIVERSE = [
    "BTC", "ETH", "SOL", "AVAX", "LINK", "DOGE", "ARB", "OP", "SUI", "BNB",
]

# --- Config -----------------------------------------------------------------
SUBREDDITS = [
    "CryptoCurrency",
    "wallstreetbets",
    "stocks",
    "StockMarket",
]

REDDIT_HOT_URL = "https://www.reddit.com/r/{sub}/hot.json?limit=100"
USER_AGENT = "HermesForge/1.0 research bot"
REQUEST_TIMEOUT = 30
REQUEST_DELAY = 1.5  # seconds between subreddit requests (be polite)

CACHE_DIR = pathlib.Path.home() / ".hermes" / "market_data" / "reddit"
CACHE_MAX_AGE_HOURS = 6  # refresh if latest snapshot older than this

# Sentiment word lists (lowercased, matched as whole words)
BULLISH_WORDS = {
    "bullish", "bull", "long", "pump", "moon", "rip", "squeeze",
    "breakout", "rally", "gain", "gains", "upside", "buy", "calls",
    "green", "ath", "soar", "surge", "rocket",
}
BEARISH_WORDS = {
    "bearish", "bear", "short", "dump", "crash", "tank", "fall",
    "drop", "loss", "losses", "downside", "sell", "puts",
    "red", "plunge", "collapse", "bleed", "rekt",
}


def _build_ticker_index():
    """Build a lookup of ticker -> compiled regex for mention matching.

    Crypto symbols are matched with a leading $ or word boundary to avoid
    common false positives (e.g. "SOL" inside "consolidate"). Stock tickers
    are matched with a leading $ or as a standalone uppercase token.
    """
    index = {}
    # Crypto first
    for sym in CRYPTO_UNIVERSE:
        # e.g. \bBTC\b or \$BTC — require boundary or $ prefix
        index[sym] = re.compile(r"(?:\$|\b)" + re.escape(sym) + r"\b", re.IGNORECASE)
    # Stocks
    for sym in get_stock_universe():
        index[sym] = re.compile(r"(?:\$|\b)" + re.escape(sym) + r"\b")
    return index


_TICKER_INDEX = _build_ticker_index()


def _count_mentions(text: str) -> dict:
    """Return {ticker: count} for tickers found in text."""
    if not text:
        return {}
    found = {}
    for sym, pattern in _TICKER_INDEX.items():
        matches = pattern.findall(text)
        if matches:
            found[sym] = len(matches)
    return found


def _score_sentiment(text: str) -> int:
    """Simple bullish(+1)/bearish(-1) word-count sentiment score."""
    if not text:
        return 0
    tokens = re.findall(r"[a-zA-Z\$]+", text.lower())
    score = 0
    for tok in tokens:
        # strip leading $ for word matching
        w = tok.lstrip("$")
        if w in BULLISH_WORDS:
            score += 1
        elif w in BEARISH_WORDS:
            score -= 1
    return score


def _normalize_sentiment(score: int) -> float:
    """Squash raw int score into [-1, 1] via tanh-like clamp."""
    if score == 0:
        return 0.0
    # clamp to [-5,5] then scale
    clamped = max(-5, min(5, score))
    return clamped / 5.0


def fetch_subreddit(subreddit: str) -> pd.DataFrame:
    """Fetch hot posts from a subreddit, return a per-post DataFrame.

    Columns: subreddit, title, selftext, score, num_comments, created_utc,
             mentions (dict), sentiment_raw (int), sentiment (float),
             ticker (list of tickers mentioned)
    """
    url = REDDIT_HOT_URL.format(sub=subreddit)
    headers = {"User-Agent": USER_AGENT}
    resp = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    payload = resp.json()

    posts = []
    children = payload.get("data", {}).get("children", [])
    for child in children:
        d = child.get("data", {})
        title = d.get("title", "") or ""
        selftext = d.get("selftext", "") or ""
        combined = f"{title}\n{selftext}"
        mentions = _count_mentions(combined)
        sent_raw = _score_sentiment(combined)
        posts.append({
            "subreddit": subreddit,
            "title": title,
            "selftext": selftext[:500],  # truncate for storage efficiency
            "score": int(d.get("score", 0)),
            "num_comments": int(d.get("num_comments", 0)),
            "created_utc": pd.Timestamp(d.get("created_utc", 0), unit="s", tz="UTC"),
            "mentions": mentions,
            "sentiment_raw": sent_raw,
            "sentiment": _normalize_sentiment(sent_raw),
            "tickers": list(mentions.keys()),
        })

    df = pd.DataFrame(posts)
    return df


def fetch_all_subreddits(force: bool = False) -> pd.DataFrame:
    """Fetch all configured subreddits. Returns concatenated per-post DataFrame.

    Uses a daily snapshot cache: if today's snapshot exists and is fresh,
    returns it instead of hitting Reddit.
    """
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    snapshot_path = CACHE_DIR / f"{today}.parquet"
    latest_path = CACHE_DIR / "latest.parquet"

    # Cache check: use latest pointer for freshness
    if not force and latest_path.exists():
        mtime = datetime.fromtimestamp(latest_path.stat().st_mtime, tz=timezone.utc)
        age_h = (datetime.now(timezone.utc) - mtime).total_seconds() / 3600
        if age_h < CACHE_MAX_AGE_HOURS:
            try:
                return pd.read_parquet(latest_path)
            except Exception:
                pass  # corrupt cache — refetch

    # Fetch fresh
    all_frames = []
    for i, sub in enumerate(SUBREDDITS):
        try:
            print(f"  fetching r/{sub} ...", file=sys.stderr)
            df = fetch_subreddit(sub)
            all_frames.append(df)
        except requests.RequestException as e:
            print(f"  WARNING: r/{sub} failed: {e}", file=sys.stderr)
        if i < len(SUBREDDITS) - 1:
            time.sleep(REQUEST_DELAY)

    if not all_frames:
        # Fallback: return whatever cached data we have, else empty
        if latest_path.exists():
            print("  no fresh data; returning cached latest", file=sys.stderr)
            return pd.read_parquet(latest_path)
        return pd.DataFrame()

    combined = pd.concat(all_frames, ignore_index=True)
    # Attach fetch timestamp
    combined["fetched_at"] = pd.Timestamp.now(tz="UTC")

    # Write daily snapshot + latest pointer
    combined.to_parquet(snapshot_path, index=False)
    combined.to_parquet(latest_path, index=False)
    print(f"  cached {len(combined)} posts to {snapshot_path}", file=sys.stderr)
    return combined


def get_reddit_summary(force: bool = False) -> dict:
    """Return a per-subreddit summary dict.

    {subreddit: {
        post_count: int,
        avg_sentiment: float (-1..1),
        top_mentions: {ticker: count}   # top 10 by mention count
    }}
    """
    df = fetch_all_subreddits(force=force)
    if df.empty:
        return {sub: {"post_count": 0, "avg_sentiment": 0.0, "top_mentions": {}}
                for sub in SUBREDDITS}

    summary = {}
    for sub in SUBREDDITS:
        sub_df = df[df["subreddit"] == sub]
        post_count = len(sub_df)
        avg_sentiment = float(sub_df["sentiment"].mean()) if post_count else 0.0

        # Aggregate mentions across posts
        mention_totals = {}
        for m in sub_df["mentions"]:
            if isinstance(m, dict):
                for ticker, cnt in m.items():
                    mention_totals[ticker] = mention_totals.get(ticker, 0) + cnt
        # Top 10
        top = dict(sorted(mention_totals.items(), key=lambda x: -x[1])[:10])

        summary[sub] = {
            "post_count": int(post_count),
            "avg_sentiment": round(avg_sentiment, 3),
            "top_mentions": {k: int(v) for k, v in top.items()},
        }
    return summary


def load_history() -> pd.DataFrame:
    """Load all daily snapshots from cache dir, concatenated chronologically."""
    if not CACHE_DIR.exists():
        return pd.DataFrame()
    frames = []
    for p in sorted(CACHE_DIR.glob("20*.parquet")):
        try:
            frames.append(pd.read_parquet(p))
        except Exception:
            continue
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Fetch Reddit sentiment feed")
    ap.add_argument("--force", action="store_true", help="Force refresh cache")
    ap.add_argument("--summary", action="store_true",
                    help="Only print summary from cache (no fetch)")
    args = ap.parse_args()

    if args.summary:
        # Load latest cache without fetching
        latest = CACHE_DIR / "latest.parquet"
        if latest.exists():
            df = pd.read_parquet(latest)
        else:
            df = pd.DataFrame()
    else:
        print("Fetching Reddit sentiment...", file=sys.stderr)
        df = fetch_all_subreddits(force=args.force)

    summary = {}
    if not df.empty:
        for sub in SUBREDDITS:
            sub_df = df[df["subreddit"] == sub]
            post_count = len(sub_df)
            avg_sentiment = float(sub_df["sentiment"].mean()) if post_count else 0.0
            mention_totals = {}
            for m in sub_df["mentions"]:
                if isinstance(m, dict):
                    for ticker, cnt in m.items():
                        mention_totals[ticker] = mention_totals.get(ticker, 0) + cnt
            top = dict(sorted(mention_totals.items(), key=lambda x: -x[1])[:10])
            summary[sub] = {
                "post_count": int(post_count),
                "avg_sentiment": round(avg_sentiment, 3),
                "top_mentions": {k: int(v) for k, v in top.items()},
            }
    else:
        for sub in SUBREDDITS:
            summary[sub] = {"post_count": 0, "avg_sentiment": 0.0, "top_mentions": {}}

    print(f"\nReddit Sentiment Summary — {len(df)} posts total")
    print("=" * 60)
    for sub in SUBREDDITS:
        s = summary[sub]
        print(f"\nr/{sub}")
        print(f"  posts: {s['post_count']}  |  avg sentiment: {s['avg_sentiment']:+.3f}")
        if s["top_mentions"]:
            top_str = ", ".join(f"{t}:{c}" for t, c in list(s["top_mentions"].items())[:8])
            print(f"  top mentions: {top_str}")
        else:
            print(f"  top mentions: (none)")
