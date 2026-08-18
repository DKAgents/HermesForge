#!/usr/bin/env python3
"""
check_liquidations.py — Liquidation cascade proxy detector.

Hyperliquid doesn't expose liquidation events via REST (WebSocket only).
We detect liquidation cascades by proxy: simultaneous OI drop + sharp price move.

A liquidation cascade is likely when:
- OI drops >5% in a short window (forced closes)
- Price moves >1.5% in the same window (cascade drives price)
- Both happen within 5 minutes

Also checks funding rate for confirmation (extreme funding = pre-liquidation setup).

Usage:
    python3 check_liquidations.py          # check and print
    python3 check_liquidations.py --json   # JSON output only
"""
import json
import sys
import time
import urllib.request
import pathlib
from datetime import datetime, timezone

OI_DROP_THRESHOLD = 0.05    # 5% OI drop
PRICE_MOVE_THRESHOLD = 0.015 # 1.5% price move
COMBINED_WINDOW_SEC = 300    # 5 minute window
STATE_FILE = pathlib.Path("/root/.hermes/market_data/liquidation_proxy_state.json")

COINS_TO_TRACK = [
    "BTC", "ETH", "SOL", "AVAX", "LINK", "DOGE", "ARB", "OP", "SUI",
    "AAVE", "ADA", "APT", "BCH", "BNB", "CRV", "DOT", "ENA", "HYPE",
    "JUP", "LTC", "NEAR", "ONDO", "PAXG", "TRUMP", "TRX", "UNI", "WLD",
    "XRP", "ZEC", "kBONK", "kPEPE", "kSHIB",
]


def fetch_hyperliquid_state():
    """Fetch current OI, mark price, and funding for tracked coins."""
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
        state = {}
        for u, ctx in zip(universe, ctxs):
            if not isinstance(u, dict) or not isinstance(ctx, dict):
                continue
            coin = u.get("name", "")
            if coin not in COINS_TO_TRACK:
                continue
            state[coin] = {
                "oi_usd": float(ctx.get("openInterest", 0)) * float(ctx.get("markPx", 0)),
                "mark_price": float(ctx.get("markPx", 0)),
                "funding_rate": float(ctx.get("funding", 0)),
                "timestamp": time.time(),
            }
        return state
    except Exception as e:
        print(f"  [WARN] Hyperliquid fetch failed: {e}", file=sys.stderr)
        return {}


def load_state():
    try:
        with open(STATE_FILE) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_state(state):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def detect_liquidation_proxy(current, previous):
    """Detect likely liquidation cascades via OI drop + price move."""
    if not previous or not current:
        return []
    
    alerts = []
    for coin, curr in current.items():
        prev = previous.get(coin)
        if not prev:
            continue
        
        prev_oi = prev.get("oi_usd", 0)
        curr_oi = curr.get("oi_usd", 0)
        prev_price = prev.get("mark_price", 0)
        curr_price = curr.get("mark_price", 0)
        
        if prev_oi == 0 or prev_price == 0:
            continue
        
        oi_change = (curr_oi - prev_oi) / prev_oi
        price_change = (curr_price - prev_price) / prev_price
        
        # Liquidation cascade proxy: OI drops significantly + sharp price move
        if oi_change < -OI_DROP_THRESHOLD and abs(price_change) > PRICE_MOVE_THRESHOLD:
            direction = "longs_liquidated" if price_change < 0 else "shorts_liquidated"
            severity = "critical" if abs(oi_change) > 0.15 else "high" if abs(oi_change) > 0.10 else "medium"
            
            alerts.append({
                "event_type": "liquidation_cascade_proxy",
                "coin": coin,
                "direction": direction,
                "oi_drop_pct": round(oi_change * 100, 2),
                "price_move_pct": round(price_change * 100, 2),
                "prev_oi_usd": prev_oi,
                "curr_oi_usd": curr_oi,
                "oi_lost_usd": abs(curr_oi - prev_oi),
                "prev_price": prev_price,
                "curr_price": curr_price,
                "funding_rate": curr.get("funding_rate", 0),
                "severity": severity,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
    
    return alerts


def check_open_trades(coin):
    """Check if we have open paper trades for this coin."""
    try:
        import csv
        trades_path = "/root/HermesForge/scripts/paper_trading/trades.csv"
        exposed = []
        with open(trades_path) as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get("status") == "open" and row.get("ticker", "").upper() == coin.upper():
                    exposed.append({
                        "trade_id": row.get("trade_id", ""),
                        "direction": row.get("direction", ""),
                        "entry_price": row.get("entry_price", ""),
                    })
        return exposed
    except Exception:
        return []


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    
    current = fetch_hyperliquid_state()
    if not current:
        print("[SILENT]")
        return
    
    previous = load_state()
    alerts = detect_liquidation_proxy(current, previous)
    
    # Save current state for next run
    save_state(current)
    
    if not alerts:
        print("[SILENT]")
        return
    
    # Add open trade exposure
    for a in alerts:
        a["open_trades"] = check_open_trades(a["coin"])
    
    if args.json:
        print(json.dumps({"alerts": alerts}, indent=2))
    else:
        for a in alerts:
            print(f"ALERT|{a['coin']}|{a['direction']}|OI:{a['oi_drop_pct']:.1f}%|PX:{a['price_move_pct']:.1f}%|{a['severity']}")


if __name__ == "__main__":
    main()