#!/usr/bin/env python3
"""
check_oi_spikes.py — Open Interest spike detector.

Tracks OI changes across Hyperliquid coins and flags when OI changes
by more than 5% in a 1-hour window. Large OI increases = new money entering,
large decreases = unwinding/liquidation events.

Usage:
    python3 check_oi_spikes.py          # check and print
    python3 check_oi_spikes.py --json   # JSON output only
"""
import json
import sys
import time
import urllib.request
import pathlib
from datetime import datetime, timezone

OI_STATE_FILE = pathlib.Path("/root/.hermes/market_data/oi_state.json")
SPIKE_THRESHOLD_PCT = 5.0  # 5% change in 1 hour
COINS_TO_TRACK = [
    "BTC", "ETH", "SOL", "AVAX", "LINK", "DOGE", "ARB", "OP", "SUI",
    "AAVE", "ADA", "APT", "BCH", "BNB", "CRV", "DOT", "ENA",
    "FARTCOIN", "HYPE", "JUP", "LTC",
    "NEAR", "ONDO", "PAXG", "PUMP", "TRUMP", "TRX", "UNI", "WLD",
    "XPL", "XRP", "ZEC", "kBONK", "kPEPE", "kSHIB",
]


def fetch_hyperliquid_oi():
    """Fetch current OI for all coins from Hyperliquid."""
    url = "https://api.hyperliquid.xyz/info"
    payload = json.dumps({"type": "metaAndAssetCtxs"}).encode()
    try:
        req = urllib.request.Request(
            url, data=payload,
            headers={"Content-Type": "application/json", "User-Agent": "HermesForge/1.0"}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
        
        if not isinstance(data, list) or len(data) < 2:
            return {}
        
        universe = data[0].get("universe", []) if isinstance(data[0], dict) else []
        ctxs = data[1] if isinstance(data[1], list) else []
        
        oi_data = {}
        for u, ctx in zip(universe, ctxs):
            if not isinstance(u, dict) or not isinstance(ctx, dict):
                continue
            coin = u.get("name", "")
            if coin not in COINS_TO_TRACK:
                continue
            oi = float(ctx.get("openInterest", 0))
            mark = float(ctx.get("markPx", 0))
            oi_usd = oi * mark
            oi_data[coin] = {
                "oi_coin": oi,
                "mark_price": mark,
                "oi_usd": oi_usd,
                "funding_rate": float(ctx.get("funding", 0)),
            }
        return oi_data
    except Exception as e:
        print(f"  [WARN] Hyperliquid OI fetch failed: {e}", file=sys.stderr)
        return {}


def load_oi_state():
    """Load previous OI snapshot."""
    try:
        with open(OI_STATE_FILE) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_oi_state(state):
    """Save current OI snapshot."""
    OI_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OI_STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def detect_spikes(current, previous):
    """Detect OI spikes by comparing current vs previous snapshot."""
    if not previous:
        return []
    
    prev_oi = previous.get("oi_data", {})
    prev_ts = previous.get("timestamp", 0)
    now_ts = time.time()
    hours_elapsed = (now_ts - prev_ts) / 3600
    
    if hours_elapsed < 0.5:
        return []  # too soon since last check
    
    spikes = []
    for coin, curr_data in current.items():
        prev_data = prev_oi.get(coin)
        if not prev_data:
            continue
        
        prev_usd = prev_data.get("oi_usd", 0)
        curr_usd = curr_data.get("oi_usd", 0)
        
        if prev_usd == 0:
            continue
        
        pct_change = ((curr_usd - prev_usd) / prev_usd) * 100
        
        if abs(pct_change) >= SPIKE_THRESHOLD_PCT:
            direction = "increase" if pct_change > 0 else "decrease"
            interpretation = "new_money" if pct_change > 0 else "unwinding"
            
            spikes.append({
                "coin": coin,
                "direction": direction,
                "pct_change": round(pct_change, 2),
                "prev_oi_usd": prev_usd,
                "curr_oi_usd": curr_usd,
                "abs_change_usd": abs(curr_usd - prev_usd),
                "hours_elapsed": round(hours_elapsed, 2),
                "interpretation": interpretation,
                "funding_rate": curr_data.get("funding_rate", 0),
                "mark_price": curr_data.get("mark_price", 0),
            })
    
    return spikes


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--threshold", type=float, default=5.0)
    args = parser.parse_args()
    
    SPIKE_THRESHOLD_PCT = args.threshold
    current_oi = fetch_hyperliquid_oi()
    if not current_oi:
        print("[SILENT]")
        return
    
    previous_state = load_oi_state()
    spikes = detect_spikes(current_oi, previous_state)
    
    # Save current state for next run
    save_oi_state({
        "timestamp": time.time(),
        "oi_data": current_oi,
    })
    
    if not spikes:
        print("[SILENT]")
        return
    
    # Sort by magnitude
    spikes.sort(key=lambda x: abs(x["pct_change"]), reverse=True)
    
    if args.json:
        print(json.dumps({"spikes": spikes}, indent=2))
    else:
        for s in spikes:
            print(f"ALERT|{s['coin']}|{s['direction']}|{s['pct_change']:.1f}%|{s['abs_change_usd']:.0f}|{s['interpretation']}")


if __name__ == "__main__":
    main()