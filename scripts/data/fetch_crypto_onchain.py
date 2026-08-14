#!/usr/bin/env python3
"""
fetch_crypto_onchain.py — Crypto on-chain & market-structure data feed

Aggregates four free (no-key) data sources into a single summary dict
suitable for the HermesForge regime filter / strategy layer:

1. BTC + ETH dominance (CoinGecko /api/v3/global)
       Rising BTC dominance = risk-off for alts. Trend computed against
       the previous daily snapshot cached on disk.

2. Altcoin Season Index (CoinGecko /api/v3/coins/markets)
       Fetch top 50 coins by mcap, count how many outperformed BTC over
       the last 7d. The API does NOT expose a 90d change on free tier, so
       per the task spec we use the 7d window (30d is also pulled as a
       secondary context field).
       >75% beating BTC  -> "altseason"
       <25% beating BTC  -> "btc_season"
       else             -> "neutral"

3. BTC blockchain stats (blockchain.info /q/*, no key)
       totalbc, 24hrtransactioncount, marketcap, 24hrbtcsent, hashrate,
       getdifficulty, bcperblock.
       NOTE: blockchain.info's legacy /q/median_tx_fee endpoint is dead
       (HTTP 404 as of 2024). Median tx fee is pulled from the free
       mempool.space /api/v1/fees/recommended endpoint instead (sat/vB).
       tx-count / fee / network-activity trends are computed against
       prior cached snapshots.

4. CryptoCompare social stats (legacy www.cryptocompare.com/api/data/
       socialstats?id=<coinId>, no key required)
       The newer min-api.cryptocompare.com/data/social/coin/* endpoints
       now require an API key (HTTP 401), so we use the legacy public
       endpoint which still returns Twitter followers, Reddit
       subscribers and GitHub stars/forks. A snapshot per coin is
       cached daily so day-over-day deltas can be tracked.

Functions exposed:
    get_crypto_onchain_summary() -> dict   # all of the above combined
    get_btc_dominance()          -> dict
    get_altcoin_season()         -> dict
    get_btc_blockchain()         -> dict
    get_crypto_social(coins=...) -> dict

Cache layout (dated JSON, one file per component per UTC day):
    ~/.hermes/market_data/crypto_onchain/
        dominance_<YYYY-MM-DD>.json
        altcoin_season_<YYYY-MM-DD>.json
        blockchain_<YYYY-MM-DD>.json
        social_<YYYY-MM-DD>.json
        summary_<YYYY-MM-DD>.json

Usage:
    python3 fetch_crypto_onchain.py              # fetch + print summary
    python3 fetch_crypto_onchain.py --force      # ignore today's cache
    python3 fetch_crypto_onchain.py --summary    # print summary only
"""

import sys
import os
import time
import json
import pathlib
import argparse
import requests
from datetime import datetime, timezone, timedelta

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

COINGECKO_GLOBAL = "https://api.coingecko.com/api/v3/global"
COINGECKO_MARKETS = "https://api.coingecko.com/api/v3/coins/markets"

BLOCKCHAIN_Q = "https://blockchain.info/q"
MEMPOOL_FEES = "https://mempool.space/api/v1/fees/recommended"

# Legacy public CryptoCompare social endpoint (no API key needed).
# The newer min-api.cryptocompare.com/data/social/coin/latest requires a key.
CRYPTOCOMPARE_SOCIAL = "https://www.cryptocompare.com/api/data/socialstats"

CACHE_DIR = pathlib.Path.home() / ".hermes" / "market_data" / "crypto_onchain"

# CoinGecko free tier is ~10-30 calls/min. We make very few calls but still
# sleep politely and retry on 429.
COINGECKO_SLEEP = 1.5
MAX_RETRIES = 3
REQUEST_TIMEOUT = 30

# Dominance / trend classification thresholds
DOMINANCE_TREND_THRESHOLD = 0.10  # percentage-point change to count as rising/falling

# Altcoin season thresholds (% of top 50 beating BTC over 7d)
ALTSEASON_HIGH = 75.0
ALTSEASON_LOW = 25.0

# Blockchain trend thresholds
TX_TREND_THRESHOLD_PCT = 5.0
FEE_TREND_THRESHOLD_PCT = 10.0

# CryptoCompare coin ids for the social endpoint (numeric ids). These are
# stable Coinpaprika/CryptoCompare internal ids. Extend freely.
# CryptoCompare numeric coin ids (verified against the public coinlist
# endpoint: https://www.cryptocompare.com/api/data/coinlist — the `Id` field
# is what socialstats expects). DO NOT guess these; wrong ids return empty
# social data silently.
CRYPTOCOMPARE_COIN_IDS = {
    "BTC": 1182,
    "ETH": 7605,
    "SOL": 934443,
    "DOGE": 4432,
    "ADA": 321992,
    "XRP": 5031,
}
# Default coin set for get_crypto_social() — BTC is the primary one per spec.
DEFAULT_SOCIAL_COINS = ["BTC", "ETH", "SOL"]

# Trend lookback: how far back to look for a prior snapshot when computing
# day-over-day trends.
TREND_LOOKBACK_DAYS = 7


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _today_utc() -> datetime:
    return _utcnow().replace(hour=0, minute=0, second=0, microsecond=0)


def _snapshot_path(component: str, day: datetime) -> pathlib.Path:
    return CACHE_DIR / f"{component}_{day.strftime('%Y-%m-%d')}.json"


def _http_get(url: str, params: dict = None, headers: dict = None,
              retries: int = MAX_RETRIES, sleep_on_retry: float = 5.0):
    """GET with retry on 429/5xx. Returns (text, status) or raises."""
    last_exc = None
    for attempt in range(retries):
        try:
            r = requests.get(url, params=params, headers=headers,
                             timeout=REQUEST_TIMEOUT)
            if r.status_code == 429 or r.status_code >= 500:
                wait = sleep_on_retry * (attempt + 1)
                print(f"  [retry] {r.status_code} on {url[:60]}... "
                      f"waiting {wait:.0f}s (attempt {attempt+1}/{retries})",
                      file=sys.stderr)
                time.sleep(wait)
                continue
            return r
        except requests.RequestException as e:
            last_exc = e
            time.sleep(sleep_on_retry)
    if last_exc:
        raise last_exc
    # Should not reach here
    raise RuntimeError(f"exhausted retries for {url}")


def _load_cached_json(path: pathlib.Path):
    if not path.exists():
        return None
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return None


def _save_json(path: pathlib.Path, data: dict) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=str)


def _load_prior_snapshot(component: str, skip_day: datetime,
                         lookback_days: int = TREND_LOOKBACK_DAYS):
    """Return the most recent cached snapshot older than `skip_day`."""
    if not CACHE_DIR.exists():
        return None
    prefix = f"{component}_"
    files = sorted(CACHE_DIR.glob(f"{prefix}*.json"))
    if not files:
        return None
    cutoff = skip_day - timedelta(days=lookback_days)
    best = None
    for f in files:
        # parse date from filename: component_YYYY-MM-DD.json
        stem = f.stem  # component_YYYY-MM-DD
        datepart = stem.split("_", 1)[1] if "_" in stem else stem
        try:
            d = datetime.strptime(datepart, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except ValueError:
            continue
        if d < skip_day and d >= cutoff:
            best = f  # keep looking for the most recent within window
        elif d < skip_day and best is None:
            best = f  # fallback to most recent before skip_day
    if best is None:
        return None
    return _load_cached_json(best)


# ---------------------------------------------------------------------------
# 1. BTC / ETH dominance
# ---------------------------------------------------------------------------

def _fetch_dominance_raw() -> dict:
    r = _http_get(COINGECKO_GLOBAL)
    r.raise_for_status()
    data = r.json().get("data", {})
    mcp = data.get("market_cap_percentage", {})
    return {
        "btc_dominance": float(mcp.get("btc") or 0.0),
        "eth_dominance": float(mcp.get("eth") or 0.0),
        "total_market_cap_usd": float(data.get("total_market_cap", {}).get("usd") or 0.0),
        "total_volume_usd": float(data.get("total_volume", {}).get("usd") or 0.0),
        "market_cap_change_24h_pct": float(data.get("market_cap_change_percentage_24h_usd") or 0.0),
        "volume_change_24h_pct": float(data.get("volume_change_percentage_24h_usd") or 0.0),
        "updated_at": _utcnow().isoformat(),
    }


def get_btc_dominance(force: bool = False) -> dict:
    """
    Get BTC + ETH dominance with trend vs prior cached snapshot.

    Returns:
        {
            "btc_dominance": float,            # %
            "eth_dominance": float,            # %
            "total_market_cap_usd": float,
            "total_volume_usd": float,
            "market_cap_change_24h_pct": float,
            "btc_dominance_trend": str,        # "rising" / "falling" / "flat"
            "btc_dominance_delta_pp": float,   # percentage-point change
            "eth_dominance_trend": str,
            "eth_dominance_delta_pp": float,
            "regime_signal": str,              # "risk_off_alts" / "risk_on_alts" / "neutral"
            "snapshot_utc": str,
            "source": "coingecko",
        }
    """
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    today = _today_utc()
    path = _snapshot_path("dominance", today)

    if not force:
        cached = _load_cached_json(path)
        if cached:
            return cached

    try:
        raw = _fetch_dominance_raw()
    except Exception as e:
        print(f"[dominance] fetch failed: {e}", file=sys.stderr)
        # fall back to cache if available
        cached = _load_cached_json(path)
        if cached:
            cached["_error"] = f"fetch failed: {e}"
            return cached
        return {
            "btc_dominance": 0.0, "eth_dominance": 0.0,
            "btc_dominance_trend": "unknown", "eth_dominance_trend": "unknown",
            "regime_signal": "unknown", "snapshot_utc": _utcnow().isoformat(),
            "source": "coingecko", "_error": str(e),
        }

    prior = _load_prior_snapshot("dominance", today)
    btc_trend, btc_delta = "flat", 0.0
    eth_trend, eth_delta = "flat", 0.0
    if prior and prior.get("btc_dominance") is not None:
        btc_delta = raw["btc_dominance"] - float(prior["btc_dominance"])
        if btc_delta > DOMINANCE_TREND_THRESHOLD:
            btc_trend = "rising"
        elif btc_delta < -DOMINANCE_TREND_THRESHOLD:
            btc_trend = "falling"
        if prior.get("eth_dominance") is not None:
            eth_delta = raw["eth_dominance"] - float(prior["eth_dominance"])
            if eth_delta > DOMINANCE_TREND_THRESHOLD:
                eth_trend = "rising"
            elif eth_delta < -DOMINANCE_TREND_THRESHOLD:
                eth_trend = "falling"

    # Rising BTC dominance = capital rotating into BTC, risk-off for alts.
    if btc_trend == "rising":
        regime = "risk_off_alts"
    elif btc_trend == "falling":
        regime = "risk_on_alts"
    else:
        regime = "neutral"

    summary = {
        "btc_dominance": round(raw["btc_dominance"], 4),
        "eth_dominance": round(raw["eth_dominance"], 4),
        "total_market_cap_usd": raw["total_market_cap_usd"],
        "total_volume_usd": raw["total_volume_usd"],
        "market_cap_change_24h_pct": round(raw["market_cap_change_24h_pct"], 2),
        "volume_change_24h_pct": round(raw["volume_change_24h_pct"], 2),
        "btc_dominance_trend": btc_trend,
        "btc_dominance_delta_pp": round(btc_delta, 4),
        "eth_dominance_trend": eth_trend,
        "eth_dominance_delta_pp": round(eth_delta, 4),
        "regime_signal": regime,
        "snapshot_utc": raw["updated_at"],
        "source": "coingecko",
    }
    _save_json(path, summary)
    return summary


# ---------------------------------------------------------------------------
# 2. Altcoin season index
# ---------------------------------------------------------------------------

def _fetch_top50_markets() -> list:
    """Fetch top 50 coins by mcap with 7d and 30d price-change fields."""
    params = {
        "vs_currency": "usd",
        "order": "market_cap_desc",
        "per_page": 50,
        "page": 1,
        "sparkline": "false",
        "price_change_percentage": "24h,7d,30d",
    }
    r = _http_get(COINGECKO_MARKETS, params=params)
    r.raise_for_status()
    return r.json()


def get_altcoin_season(force: bool = False) -> dict:
    """
    Altcoin Season Index: % of top-50 coins (by mcap) that outperformed BTC
    over the last 7 days (CoinGecko free tier exposes 7d and 30d, not 90d).

    Classification:
        >= 75% beating BTC  -> "altseason"
        <= 25% beating BTC  -> "btc_season"
        else                -> "neutral"

    Returns:
        {
            "index_value": float,             # 0-100, % beating BTC over 7d
            "classification": str,             # altseason / btc_season / neutral
            "coins_beating_btc_7d": int,
            "coins_beating_btc_30d": int,
            "total_coins": int,
            "btc_7d_change_pct": float,
            "btc_30d_change_pct": float,
            "index_value_30d": float,          # % beating BTC over 30d
            "top_performers_7d": [ {symbol, pct} ... ],  # top 5
            "top_laggards_7d":  [ {symbol, pct} ... ],   # bottom 5
            "snapshot_utc": str,
            "source": "coingecko",
        }
    """
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    today = _today_utc()
    path = _snapshot_path("altcoin_season", today)

    if not force:
        cached = _load_cached_json(path)
        if cached:
            return cached

    try:
        time.sleep(COINGECKO_SLEEP)
        markets = _fetch_top50_markets()
    except Exception as e:
        print(f"[altcoin_season] fetch failed: {e}", file=sys.stderr)
        cached = _load_cached_json(path)
        if cached:
            cached["_error"] = f"fetch failed: {e}"
            return cached
        return {
            "index_value": 0.0, "classification": "unknown",
            "coins_beating_btc_7d": 0, "coins_beating_btc_30d": 0,
            "total_coins": 0, "snapshot_utc": _utcnow().isoformat(),
            "source": "coingecko", "_error": str(e),
        }

    # Find BTC row
    btc_row = None
    for item in markets:
        if item.get("id") == "bitcoin":
            btc_row = item
            break
    btc_7d = float((btc_row or {}).get("price_change_percentage_7d_in_currency") or 0.0)
    btc_30d = float((btc_row or {}).get("price_change_percentage_30d_in_currency") or 0.0)

    coins = []
    for item in markets:
        sym = (item.get("symbol") or item.get("id") or "").upper()
        ch7 = float(item.get("price_change_percentage_7d_in_currency") or 0.0)
        ch30 = float(item.get("price_change_percentage_30d_in_currency") or 0.0)
        coins.append({
            "symbol": sym, "id": item.get("id"),
            "change_7d": ch7, "change_30d": ch30,
            "market_cap": float(item.get("market_cap") or 0.0),
        })

    beating_7d = [c for c in coins if c["change_7d"] > btc_7d]
    beating_30d = [c for c in coins if c["change_30d"] > btc_30d]
    n = len(coins) or 1
    index_7d = (len(beating_7d) / n) * 100.0
    index_30d = (len(beating_30d) / n) * 100.0

    if index_7d >= ALTSEASON_HIGH:
        classification = "altseason"
    elif index_7d <= ALTSEASON_LOW:
        classification = "btc_season"
    else:
        classification = "neutral"

    ranked = sorted(coins, key=lambda c: c["change_7d"], reverse=True)
    top5 = [{"symbol": c["symbol"], "change_7d_pct": round(c["change_7d"], 2)} for c in ranked[:5]]
    bot5 = [{"symbol": c["symbol"], "change_7d_pct": round(c["change_7d"], 2)} for c in ranked[-5:]]

    summary = {
        "index_value": round(index_7d, 2),
        "classification": classification,
        "coins_beating_btc_7d": len(beating_7d),
        "coins_beating_btc_30d": len(beating_30d),
        "total_coins": len(coins),
        "btc_7d_change_pct": round(btc_7d, 2),
        "btc_30d_change_pct": round(btc_30d, 2),
        "index_value_30d": round(index_30d, 2),
        "classification_30d": (
            "altseason" if index_30d >= ALTSEASON_HIGH
            else "btc_season" if index_30d <= ALTSEASON_LOW
            else "neutral"
        ),
        "top_performers_7d": top5,
        "top_laggards_7d": bot5,
        "snapshot_utc": _utcnow().isoformat(),
        "source": "coingecko",
    }
    _save_json(path, summary)
    return summary


# ---------------------------------------------------------------------------
# 3. BTC blockchain stats (blockchain.info + mempool.space fallback)
# ---------------------------------------------------------------------------

def _fetch_blockchain_q(endpoint: str):
    """Fetch a single blockchain.info /q endpoint. Returns raw text or None."""
    try:
        r = _http_get(f"{BLOCKCHAIN_Q}/{endpoint}", retries=2, sleep_on_retry=3.0)
        if r.status_code == 200:
            return r.text.strip()
        return None
    except Exception:
        return None


def _fetch_mempool_fees() -> dict:
    """Fallback fee source (blockchain.info /q/median_tx_fee is dead)."""
    try:
        r = _http_get(MEMPOOL_FEES, retries=2, sleep_on_retry=3.0)
        if r.status_code == 200:
            d = r.json()
            return {
                "fastest_fee_sat_vb": int(d.get("fastestFee") or 0),
                "half_hour_fee_sat_vb": int(d.get("halfHourFee") or 0),
                "hour_fee_sat_vb": int(d.get("hourFee") or 0),
                "economy_fee_sat_vb": int(d.get("economyFee") or 0),
                "minimum_fee_sat_vb": int(d.get("minimumFee") or 0),
                "source": "mempool.space",
            }
    except Exception:
        pass
    return {
        "fastest_fee_sat_vb": None, "half_hour_fee_sat_vb": None,
        "hour_fee_sat_vb": None, "economy_fee_sat_vb": None,
        "minimum_fee_sat_vb": None, "source": "mempool.space",
    }


def _to_float(val):
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


def _to_int(val):
    try:
        return int(float(val))
    except (TypeError, ValueError):
        return None


def get_btc_blockchain(force: bool = False) -> dict:
    """
    BTC blockchain stats from blockchain.info /q (no key) + mempool.space
    for fees (blockchain.info /q/median_tx_fee is dead).

    Returns:
        {
            "total_btc_circulating": int,      # satoshis (blockchain.info totalbc)
            "total_btc_circulating_btc": float,# BTC
            "tx_count_24h": int,
            "btc_sent_24h_satoshi": int,       # 24hrbtcsent
            "market_cap_usd": float,
            "hashrate": float,                 # GH/s
            "difficulty": float,
            "block_subsidy_btc": float,        # bcperblock
            "fees": { sat/vB fields ... },
            "median_fee_sat_vb": int,          # convenience: hour fee
            "tx_count_trend": str,            # rising/falling/flat vs prior
            "tx_count_delta_pct": float,
            "fee_trend": str,
            "fee_delta_pct": float,
            "network_activity_score": float,   # 0-100 composite
            "snapshot_utc": str,
            "source": "blockchain.info + mempool.space",
        }
    """
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    today = _today_utc()
    path = _snapshot_path("blockchain", today)

    if not force:
        cached = _load_cached_json(path)
        if cached:
            return cached

    totalbc = _fetch_blockchain_q("totalbc")
    txcount = _fetch_blockchain_q("24hrtransactioncount")
    marketcap = _fetch_blockchain_q("marketcap")
    btcsent = _fetch_blockchain_q("24hrbtcsent")
    hashrate = _fetch_blockchain_q("hashrate")
    difficulty = _fetch_blockchain_q("getdifficulty")
    bcperblock = _fetch_blockchain_q("bcperblock")
    fees = _fetch_mempool_fees()

    total_btc_sat = _to_int(totalbc)
    total_btc = (total_btc_sat / 1e8) if total_btc_sat is not None else None
    summary = {
        "total_btc_circulating_satoshi": total_btc_sat,
        "total_btc_circulating_btc": total_btc,
        "tx_count_24h": _to_int(txcount),
        "btc_sent_24h_satoshi": _to_int(btcsent),
        "btc_sent_24h_btc": (_to_int(btcsent) / 1e8) if _to_int(btcsent) is not None else None,
        "market_cap_usd": _to_float(marketcap),
        "hashrate": _to_float(hashrate),
        "difficulty": _to_float(difficulty),
        "block_subsidy_btc": (_to_float(bcperblock) if _to_float(bcperblock) is not None else None),
        "fees": fees,
        # convenience: hour-fee as the "median" fee proxy
        "median_fee_sat_vb": fees.get("hour_fee_sat_vb"),
        "snapshot_utc": _utcnow().isoformat(),
        "source": "blockchain.info + mempool.space",
    }

    # Trends vs prior snapshot
    prior = _load_prior_snapshot("blockchain", today)
    tx_trend, tx_delta = "flat", 0.0
    fee_trend, fee_delta = "flat", 0.0
    if prior:
        prev_tx = prior.get("tx_count_24h")
        if prev_tx is not None and summary["tx_count_24h"] is not None and prev_tx > 0:
            tx_delta = (summary["tx_count_24h"] - prev_tx) / prev_tx * 100.0
            if tx_delta > TX_TREND_THRESHOLD_PCT:
                tx_trend = "rising"
            elif tx_delta < -TX_TREND_THRESHOLD_PCT:
                tx_trend = "falling"
        prev_fee = prior.get("median_fee_sat_vb")
        cur_fee = summary["median_fee_sat_vb"]
        if prev_fee and cur_fee is not None and prev_fee > 0:
            fee_delta = (cur_fee - prev_fee) / prev_fee * 100.0
            if fee_delta > FEE_TREND_THRESHOLD_PCT:
                fee_trend = "rising"
            elif fee_delta < -FEE_TREND_THRESHOLD_PCT:
                fee_trend = "falling"
    summary["tx_count_trend"] = tx_trend
    summary["tx_count_delta_pct"] = round(tx_delta, 2)
    summary["fee_trend"] = fee_trend
    summary["fee_delta_pct"] = round(fee_delta, 2)

    # Network activity score (0-100). Combines tx count trend, fee level,
    # and btc sent activity. Heuristic composite.
    tx_score = 50.0
    if summary["tx_count_24h"] is not None:
        # typical 24h tx count ~ 300k-400k; normalize around 350k
        tx_score = min(100.0, max(0.0, (summary["tx_count_24h"] / 500000.0) * 100.0))
    fee_score = 50.0
    cur_fee = summary["median_fee_sat_vb"]
    if cur_fee is not None:
        # typical median fee 1-50 sat/vB; normalize around 20
        fee_score = min(100.0, max(0.0, (cur_fee / 40.0) * 100.0))
    trend_bonus = 0.0
    if tx_trend == "rising":
        trend_bonus += 10.0
    elif tx_trend == "falling":
        trend_bonus -= 10.0
    if fee_trend == "rising":
        trend_bonus += 5.0
    elif fee_trend == "falling":
        trend_bonus -= 5.0
    activity = max(0.0, min(100.0, 0.5 * tx_score + 0.5 * fee_score + trend_bonus))
    summary["network_activity_score"] = round(activity, 2)

    _save_json(path, summary)
    return summary


# ---------------------------------------------------------------------------
# 4. CryptoCompare social stats
# ---------------------------------------------------------------------------

def _fetch_cryptocompare_social(coin_id: int) -> dict:
    """Fetch social stats for one CryptoCompare coin id (legacy no-key endpoint)."""
    r = _http_get(CRYPTOCOMPARE_SOCIAL, params={"id": coin_id}, retries=2)
    r.raise_for_status()
    payload = r.json()
    if payload.get("Response") != "Success":
        raise RuntimeError(f"cryptocompare social failed: {payload.get('Message')}")
    return payload.get("Data", {})


def get_crypto_social(coins: list = None, force: bool = False) -> dict:
    """
    Per-coin social stats from CryptoCompare (legacy public endpoint, no key).

    Returns:
        {
            "<SYMBOL>": {
                "name": str,
                "twitter_followers": int,
                "twitter_statuses": int,
                "twitter_following": int,
                "reddit_subscribers": int,
                "reddit_active_users": int,
                "reddit_posts_per_day": float,
                "reddit_comments_per_day": float,
                "github_repos": int,
                "github_stars": int,        # summed across repos
                "github_forks": int,
                "github_contributors": int,
                "github_open_issues": int,
                "cryptocompare_followers": int,
                "facebook_likes": int,
                "points": int,             # CryptoCompare composite score
                "snapshot_utc": str,
            },
            ...
            "snapshot_utc": str,
            "source": "cryptocompare",
        }
    """
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    today = _today_utc()
    path = _snapshot_path("social", today)

    if not force:
        cached = _load_cached_json(path)
        if cached:
            return cached

    if coins is None:
        coins = DEFAULT_SOCIAL_COINS

    out: dict = {}
    for sym in coins:
        cid = CRYPTOCOMPARE_COIN_IDS.get(sym.upper())
        if cid is None:
            out[sym.upper()] = {"error": f"no CryptoCompare id mapped for {sym}"}
            continue
        try:
            data = _fetch_cryptocompare_social(cid)
            tw = data.get("Twitter", {}) or {}
            rd = data.get("Reddit", {}) or {}
            cc = data.get("CryptoCompare", {}) or {}
            fb = data.get("Facebook", {}) or {}
            general = data.get("General", {}) or {}
            repos = data.get("CodeRepository", {}).get("List", []) or []

            stars = sum(int(r.get("stars") or 0) for r in repos)
            forks = sum(int(r.get("forks") or 0) for r in repos)
            contributors = sum(int(r.get("contributors") or 0) for r in repos)
            open_issues = sum(int(r.get("open_issues") or 0) for r in repos)
            repo_urls = [r.get("url") for r in repos if r.get("url")]

            out[sym.upper()] = {
                "name": general.get("CoinName") or sym.upper(),
                "twitter_followers": int(tw.get("followers") or 0),
                "twitter_statuses": int(tw.get("statuses") or 0),
                "twitter_following": int(tw.get("following") or 0),
                "twitter_link": tw.get("link"),
                "reddit_subscribers": int(rd.get("subscribers") or 0),
                "reddit_active_users": int(rd.get("active_users") or 0),
                "reddit_posts_per_day": float(rd.get("posts_per_day") or 0.0),
                "reddit_comments_per_day": float(rd.get("comments_per_day") or 0.0),
                "reddit_link": rd.get("link"),
                "github_repos": len(repos),
                "github_stars": stars,
                "github_forks": forks,
                "github_contributors": contributors,
                "github_open_issues": open_issues,
                "github_repo_urls": repo_urls,
                "cryptocompare_followers": int(cc.get("Followers") or 0),
                "cryptocompare_posts": int(cc.get("Posts") or 0),
                "facebook_likes": int(fb.get("likes") or 0),
                "points": int(general.get("Points") or 0),
                "snapshot_utc": _utcnow().isoformat(),
            }
        except Exception as e:
            out[sym.upper()] = {"error": str(e), "snapshot_utc": _utcnow().isoformat()}
        time.sleep(0.5)  # be gentle

    payload = {
        **out,
        "snapshot_utc": _utcnow().isoformat(),
        "source": "cryptocompare",
    }
    _save_json(path, payload)
    return payload


# ---------------------------------------------------------------------------
# Combined summary
# ---------------------------------------------------------------------------

def get_crypto_onchain_summary(force: bool = False, social_coins: list = None) -> dict:
    """
    Aggregate on-chain + market-structure summary. Calls each component
    (each uses its own daily cache, so repeated calls are cheap).

    Returns a dict with keys:
        btc_dominance, altcoin_season, btc_blockchain, crypto_social,
        snapshot_utc, source
    """
    dominance = get_btc_dominance(force=force)
    time.sleep(COINGECKO_SLEEP)
    altseason = get_altcoin_season(force=force)
    time.sleep(COINGECKO_SLEEP)
    blockchain = get_btc_blockchain(force=force)
    social = get_crypto_social(coins=social_coins, force=force)

    return {
        "btc_dominance": dominance,
        "altcoin_season": altseason,
        "btc_blockchain": blockchain,
        "crypto_social": social,
        "snapshot_utc": _utcnow().isoformat(),
        "source": "coingecko + blockchain.info + mempool.space + cryptocompare",
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _fmt_btc(v):
    if v is None:
        return "n/a"
    if v >= 1e9:
        return f"{v/1e9:.2f}B BTC"
    if v >= 1e6:
        return f"{v/1e6:.2f}M BTC"
    return f"{v:,.0f} BTC"


def _fmt_usd(v):
    if v is None:
        return "n/a"
    if v >= 1e12:
        return f"${v/1e12:.2f}T"
    if v >= 1e9:
        return f"${v/1e9:.2f}B"
    if v >= 1e6:
        return f"${v/1e6:.1f}M"
    return f"${v:,.0f}"


def _print_summary(s: dict) -> None:
    print("\n=== Crypto On-Chain Summary ===")
    print(f"snapshot: {s['snapshot_utc']}")

    d = s["btc_dominance"]
    print("\n--- BTC / ETH Dominance (CoinGecko) ---")
    print(f"  BTC dominance : {d.get('btc_dominance','?')}%  (trend: {d.get('btc_dominance_trend')}, "
          f"Δ {d.get('btc_dominance_delta_pp','?'):+}pp)")
    print(f"  ETH dominance : {d.get('eth_dominance','?')}%  (trend: {d.get('eth_dominance_trend')}, "
          f"Δ {d.get('eth_dominance_delta_pp','?'):+}pp)")
    print(f"  Total mcap    : {_fmt_usd(d.get('total_market_cap_usd'))}  "
          f"(24h: {d.get('market_cap_change_24h_pct','?'):+}%)")
    print(f"  Regime signal : {d.get('regime_signal')}")

    a = s["altcoin_season"]
    print("\n--- Altcoin Season Index ---")
    print(f"  Index (7d)  : {a.get('index_value','?')}% beating BTC  ->  {a.get('classification')}")
    print(f"  Index (30d) : {a.get('index_value_30d','?')}%  ->  {a.get('classification_30d')}")
    print(f"  BTC 7d: {a.get('btc_7d_change_pct','?')}%   BTC 30d: {a.get('btc_30d_change_pct','?')}%")
    print(f"  Coins beating BTC: {a.get('coins_beating_btc_7d','?')}/{a.get('total_coins','?')} (7d),  "
          f"{a.get('coins_beating_btc_30d','?')}/{a.get('total_coins','?')} (30d)")
    print(f"  Top 7d : {a.get('top_performers_7d')}")
    print(f"  Bot 7d : {a.get('top_laggards_7d')}")

    b = s["btc_blockchain"]
    print("\n--- BTC Blockchain (blockchain.info + mempool.space) ---")
    print(f"  Circulating : {_fmt_btc(b.get('total_btc_circulating_btc'))}")
    print(f"  24h tx count: {b.get('tx_count_24h','?')}  (trend: {b.get('tx_count_trend')}, "
          f"Δ {b.get('tx_count_delta_pct','?'):+}%)")
    print(f"  24h BTC sent: {_fmt_btc(b.get('btc_sent_24h_btc'))}")
    print(f"  Market cap  : {_fmt_usd(b.get('market_cap_usd'))}")
    print(f"  Hashrate    : {b.get('hashrate','?')} GH/s")
    print(f"  Difficulty  : {b.get('difficulty','?')}")
    print(f"  Block subsidy: {b.get('block_subsidy_btc','?')} BTC")
    fees = b.get("fees", {})
    print(f"  Fees (sat/vB): fastest={fees.get('fastest_fee_sat_vb')} "
          f"halfHour={fees.get('half_hour_fee_sat_vb')} hour={fees.get('hour_fee_sat_vb')} "
          f"economy={fees.get('economy_fee_sat_vb')}")
    print(f"  Fee trend   : {b.get('fee_trend')} (Δ {b.get('fee_delta_pct','?'):+}%)")
    print(f"  Network activity score: {b.get('network_activity_score','?')}/100")

    soc = s["crypto_social"]
    print("\n--- Crypto Social (CryptoCompare) ---")
    for key, val in soc.items():
        if key in ("snapshot_utc", "source"):
            continue
        if not isinstance(val, dict):
            continue
        if "error" in val:
            print(f"  {key}: ERROR {val['error']}")
            continue
        print(f"  {key}: tw={val.get('twitter_followers','?')} "
              f"reddit={val.get('reddit_subscribers','?')} "
              f"gh_stars={val.get('github_stars','?')} "
              f"gh_forks={val.get('github_forks','?')}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Fetch crypto on-chain & market-structure data")
    ap.add_argument("--force", action="store_true", help="Ignore today's cache, fetch fresh")
    ap.add_argument("--summary", action="store_true", help="Print summary only")
    ap.add_argument("--coins", nargs="*", default=None,
                    help="Coins for social stats (default: BTC ETH SOL)")
    args = ap.parse_args()

    summary = get_crypto_onchain_summary(force=args.force, social_coins=args.coins)
    _print_summary(summary)

    # Also persist a combined summary snapshot
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    today = _today_utc()
    combined_path = _snapshot_path("summary", today)
    _save_json(combined_path, summary)
    print(f"\nCombined summary cached to {combined_path}", file=sys.stderr)
