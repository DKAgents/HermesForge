#!/usr/bin/env python3
"""
fetch_defillama.py — DeFi Total Value Locked (TVL) via DeFiLlama

Free API, no key required.
  - https://api.llama.fi/v2/chains     → TVL per chain
  - https://api.llama.fi/protocols     → protocol-level TVL

Caches daily snapshots to ~/.hermes/market_data/defillama/<YYYY-MM-DD>.parquet
Refreshes if no snapshot exists for today.

Usage:
    python3 fetch_defillama.py              # fetch/update today's snapshot
    python3 fetch_defillama.py --force      # force refresh today's snapshot
    python3 fetch_defillama.py --summary    # print TVL summary only
"""

import sys
import pathlib
import argparse
import requests
import pandas as pd
from datetime import datetime, timezone, timedelta

CHAINS_URL = "https://api.llama.fi/v2/chains"
PROTOCOLS_URL = "https://api.llama.fi/protocols"

CACHE_DIR = pathlib.Path.home() / ".hermes" / "market_data" / "defillama"

# Chains tracked for the per-chain breakdown. Names must match the `name`
# field returned by /v2/chains exactly (verified against live API).
MAJOR_CHAINS = [
    "Ethereum",
    "Solana",
    "Arbitrum",
    "Optimism",
    "BSC",
    "Base",
    "Avalanche",
]

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


def fetch_tvl() -> pd.DataFrame:
    """
    Fetch current TVL snapshot from DeFiLlama.

    Returns a single-row DataFrame with columns:
        snapshot_utc, total_tvl, <chain>_tvl for each MAJOR_CHAIN,
        chains_reported, protocols_reported
    """
    resp = requests.get(CHAINS_URL, timeout=30)
    resp.raise_for_status()
    chains = resp.json()

    total_tvl = float(sum(c.get("tvl", 0) for c in chains))

    chain_tvls = {}
    by_name = {c["name"]: c for c in chains}
    for chain in MAJOR_CHAINS:
        chain_tvls[chain] = float(by_name.get(chain, {}).get("tvl", 0.0))

    # protocol count is a nice-to-have; failure shouldn't break the snapshot
    protocols_reported = 0
    try:
        presp = requests.get(PROTOCOLS_URL, timeout=30)
        presp.raise_for_status()
        protocols_reported = len(presp.json())
    except Exception as e:  # noqa: BLE001
        print(f"DeFiLlama: protocols endpoint failed ({e})", file=sys.stderr)

    row = {
        "snapshot_utc": pd.Timestamp(datetime.now(timezone.utc)),
        "total_tvl": total_tvl,
        "chains_reported": len(chains),
        "protocols_reported": protocols_reported,
    }
    for chain, val in chain_tvls.items():
        row[f"{chain}_tvl"] = val

    return pd.DataFrame([row])


def load_tvl(force: bool = False) -> pd.DataFrame:
    """
    Load today's TVL snapshot from cache or fetch fresh.

    Daily snapshot scheme: one parquet per UTC day. If today's snapshot
    already exists it is reused unless force=True.
    """
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    today = _today_utc()
    path = _snapshot_path(today)

    if not force and path.exists():
        return pd.read_parquet(path)

    df = fetch_tvl()
    df.to_parquet(path, index=False)
    print(f"DeFiLlama TVL: snapshot cached to {path}", file=sys.stderr)
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


def get_tvl_summary(force: bool = False) -> dict:
    """
    Build a TVL summary suitable for downstream strategy/agent consumption.

    Returns:
        {
            "total_tvl": float,                  # USD
            "chain_tvls": {chain: float, ...},   # major chains only
            "trend": str,                        # "up" / "down" / "flat"
            "trend_pct": float,                  # % change vs ~7d ago
            "snapshot_utc": str,                 # ISO timestamp
            "chains_reported": int,
            "protocols_reported": int,
        }
    """
    df = load_tvl(force=force)
    if df.empty:
        return {
            "total_tvl": 0.0,
            "chain_tvls": {},
            "trend": "flat",
            "trend_pct": 0.0,
            "snapshot_utc": "",
            "chains_reported": 0,
            "protocols_reported": 0,
        }

    latest = df.iloc[-1]
    total_tvl = float(latest["total_tvl"])
    chain_tvls = {
        chain: float(latest.get(f"{chain}_tvl", 0.0)) for chain in MAJOR_CHAINS
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
        prev_total = float(past["total_tvl"].iloc[-1])
        if prev_total > 0:
            trend_pct = (total_tvl - prev_total) / prev_total * 100.0
            if trend_pct > TREND_THRESHOLD_PCT:
                trend = "up"
            elif trend_pct < -TREND_THRESHOLD_PCT:
                trend = "down"
            else:
                trend = "flat"

    return {
        "total_tvl": total_tvl,
        "chain_tvls": chain_tvls,
        "trend": trend,
        "trend_pct": round(trend_pct, 2),
        "snapshot_utc": str(latest["snapshot_utc"]),
        "chains_reported": int(latest.get("chains_reported", 0)),
        "protocols_reported": int(latest.get("protocols_reported", 0)),
    }


def _fmt_usd(v: float) -> str:
    if v >= 1e9:
        return f"${v / 1e9:.2f}B"
    if v >= 1e6:
        return f"${v / 1e6:.1f}M"
    return f"${v:,.0f}"


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Fetch DeFiLlama TVL data")
    ap.add_argument("--force", action="store_true", help="Force refresh today's snapshot")
    ap.add_argument("--summary", action="store_true", help="Print TVL summary only")
    args = ap.parse_args()

    if args.summary:
        s = get_tvl_summary(force=args.force)
        print(f"\nDeFiLlama TVL Summary — {s['snapshot_utc']}")
        print(f"  Total TVL: {_fmt_usd(s['total_tvl'])}  (trend: {s['trend']}, {s['trend_pct']:+.2f}%)")
        print(f"  Chains reported: {s['chains_reported']}  Protocols: {s['protocols_reported']}")
        print(f"  Major-chain TVL:")
        for chain, val in sorted(s["chain_tvls"].items(), key=lambda kv: -kv[1]):
            share = (val / s["total_tvl"] * 100.0) if s["total_tvl"] else 0.0
            print(f"    {chain:<10} {_fmt_usd(val):>10}  ({share:5.1f}%)")
    else:
        df = load_tvl(force=args.force)
        print(f"\nDeFiLlama TVL — snapshot {df.iloc[0]['snapshot_utc']}")
        print(f"  Total TVL: {_fmt_usd(df.iloc[0]['total_tvl'])}")
        print(f"  Chains reported: {df.iloc[0]['chains_reported']}")
        print(f"  Protocols reported: {df.iloc[0]['protocols_reported']}")
        print(f"\n  Major-chain TVL:")
        for chain in MAJOR_CHAINS:
            val = df.iloc[0].get(f"{chain}_tvl", 0.0)
            print(f"    {chain:<10} {_fmt_usd(val):>10}")
