#!/usr/bin/env python3
"""
fetch_stablecoin_supply.py — Stablecoin market cap / total supply via CoinGecko

Free API, no key required.
  - https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&ids=...

Market cap of major stablecoins (USDT, USDC, DAI, BUSD, FRAX) is a proxy for
total capital parked in crypto — a rising aggregate supply signals net capital
inflow, a falling one signals net outflow.

Caches daily snapshots to ~/.hermes/market_data/stablecoin/<YYYY-MM-DD>.parquet
Refreshes if no snapshot exists for today.

Usage:
    python3 fetch_stablecoin_supply.py              # fetch/update today's snapshot
    python3 fetch_stablecoin_supply.py --force      # force refresh today's snapshot
    python3 fetch_stablecoin_supply.py --summary    # print stablecoin summary only
"""

import sys
import pathlib
import argparse
import requests
import pandas as pd
from datetime import datetime, timezone, timedelta

API_URL = "https://api.coingecko.com/api/v3/coins/markets"
VS_CURRENCY = "usd"

# CoinGecko `ids` for the stablecoins we track. Order is preserved so the
# snapshot columns have a stable layout. These map to the {name: market_cap}
# keys returned by get_stablecoin_summary().
COINS = [
    ("tether", "USDT"),
    ("usd-coin", "USDC"),
    ("dai", "DAI"),
    ("binance-usd", "BUSD"),
    ("frax", "FRAX"),
]
COIN_IDS = [c[0] for c in COINS]
COIN_TICKERS = [c[1] for c in COINS]

CACHE_DIR = pathlib.Path.home() / ".hermes" / "market_data" / "stablecoin"

# Trend is computed from snapshots taken ~7 days apart. A |Δ%| below this
# threshold is reported as "flat".
TREND_THRESHOLD_PCT = 1.0
TREND_LOOKBACK_DAYS = 7


def _snapshot_path(day: datetime) -> pathlib.Path:
    """Parquet path for a given UTC day."""
    return CACHE_DIR / f"{day.strftime('%Y-%m-%d')}.parquet"


def _today_utc() -> datetime:
    return datetime.now(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    )


def fetch_stablecoin_supply() -> pd.DataFrame:
    """
    Fetch current stablecoin market-cap snapshot from CoinGecko.

    Returns a single-row DataFrame with columns:
        snapshot_utc, total_supply, <TICKER>_market_cap for each tracked coin,
        coins_reported
    """
    params = {
        "vs_currency": VS_CURRENCY,
        "ids": ",".join(COIN_IDS),
        "order": "market_cap_desc",
        "per_page": len(COIN_IDS),
        "page": 1,
        "sparkline": "false",
        "price_change_percentage": "",
    }
    resp = requests.get(API_URL, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    by_id = {item["id"]: item for item in data}

    row = {
        "snapshot_utc": pd.Timestamp(datetime.now(timezone.utc)),
        "total_supply": 0.0,
        "coins_reported": 0,
    }
    total = 0.0
    reported = 0
    for coin_id, ticker in COINS:
        item = by_id.get(coin_id)
        mcap = float(item["market_cap"]) if item and item.get("market_cap") is not None else 0.0
        row[f"{ticker}_market_cap"] = mcap
        total += mcap
        if mcap > 0:
            reported += 1
    row["total_supply"] = total
    row["coins_reported"] = reported

    return pd.DataFrame([row])


def load_stablecoin_supply(force: bool = False) -> pd.DataFrame:
    """
    Load today's stablecoin snapshot from cache or fetch fresh.

    Daily snapshot scheme: one parquet per UTC day. If today's snapshot
    already exists it is reused unless force=True.
    """
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    today = _today_utc()
    path = _snapshot_path(today)

    if not force and path.exists():
        return pd.read_parquet(path)

    df = fetch_stablecoin_supply()
    df.to_parquet(path, index=False)
    print(f"Stablecoin supply: snapshot cached to {path}", file=sys.stderr)
    return df


def _load_history(days: int = 30) -> pd.DataFrame:
    """Concatenate the most recent `days` daily snapshot parquets."""
    if not CACHE_DIR.exists():
        return pd.DataFrame()
    files = sorted(CACHE_DIR.glob("*.parquet"))
    if not files:
        return pd.DataFrame()
    recent = files[-days:]
    frames = []
    for f in recent:
        try:
            frames.append(pd.read_parquet(f))
        except Exception:  # noqa: BLE001
            continue
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True).sort_values("snapshot_utc")


def get_stablecoin_summary(force: bool = False) -> dict:
    """
    Build a stablecoin summary suitable for the regime filter / downstream
    strategy consumption.

    Returns:
        {
            "total_supply": float,                  # USD market cap across tracked coins
            "coins": {ticker: float, ...},          # market cap per tracked stablecoin
            "trend": str,                            # "up" / "down" / "flat"
            "trend_pct": float,                      # % change vs ~7d ago
            "snapshot_utc": str,                      # ISO timestamp
            "coins_reported": int,
        }
    """
    df = load_stablecoin_supply(force=force)
    if df.empty:
        return {
            "total_supply": 0.0,
            "coins": {},
            "trend": "flat",
            "trend_pct": 0.0,
            "snapshot_utc": "",
            "coins_reported": 0,
        }

    latest = df.iloc[-1]
    total_supply = float(latest["total_supply"])
    coins = {
        ticker: float(latest.get(f"{ticker}_market_cap", 0.0))
        for _, ticker in COINS
    }

    # Trend from history: compare latest vs snapshot ~7 days ago.
    trend = "flat"
    trend_pct = 0.0
    hist = _load_history(days=TREND_LOOKBACK_DAYS + 5)
    if len(hist) >= 2:
        now_ts = pd.Timestamp(latest["snapshot_utc"])
        cutoff = now_ts - timedelta(days=TREND_LOOKBACK_DAYS)
        past = hist[hist["snapshot_utc"] <= cutoff]
        if past.empty:
            past = hist.iloc[[0]]
        prev_total = float(past["total_supply"].iloc[-1])
        if prev_total > 0:
            trend_pct = (total_supply - prev_total) / prev_total * 100.0
            if trend_pct > TREND_THRESHOLD_PCT:
                trend = "up"
            elif trend_pct < -TREND_THRESHOLD_PCT:
                trend = "down"
            else:
                trend = "flat"

    return {
        "total_supply": total_supply,
        "coins": coins,
        "trend": trend,
        "trend_pct": round(trend_pct, 2),
        "snapshot_utc": str(latest["snapshot_utc"]),
        "coins_reported": int(latest.get("coins_reported", 0)),
    }


def _fmt_usd(v: float) -> str:
    if v >= 1e9:
        return f"${v / 1e9:.2f}B"
    if v >= 1e6:
        return f"${v / 1e6:.1f}M"
    return f"${v:,.0f}"


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Fetch stablecoin market-cap / supply data (CoinGecko)")
    ap.add_argument("--force", action="store_true", help="Force refresh today's snapshot")
    ap.add_argument("--summary", action="store_true", help="Print stablecoin summary only")
    args = ap.parse_args()

    if args.summary:
        s = get_stablecoin_summary(force=args.force)
        print(f"\nStablecoin Summary — {s['snapshot_utc']}")
        print(f"  Total supply: {_fmt_usd(s['total_supply'])}  (trend: {s['trend']}, {s['trend_pct']:+.2f}%)")
        print(f"  Coins reported: {s['coins_reported']}")
        print(f"  Per-coin market cap:")
        for ticker, val in sorted(s["coins"].items(), key=lambda kv: -kv[1]):
            share = (val / s["total_supply"] * 100.0) if s["total_supply"] else 0.0
            print(f"    {ticker:<6} {_fmt_usd(val):>12}  ({share:5.1f}%)")
    else:
        df = load_stablecoin_supply(force=args.force)
        row = df.iloc[0]
        print(f"\nStablecoin Supply — snapshot {row['snapshot_utc']}")
        print(f"  Total market cap: {_fmt_usd(row['total_supply'])}")
        print(f"  Coins reported: {row['coins_reported']}")
        print(f"\n  Per-coin market cap:")
        for _, ticker in COINS:
            val = row.get(f"{ticker}_market_cap", 0.0)
            print(f"    {ticker:<6} {_fmt_usd(val):>12}")
