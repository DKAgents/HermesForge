#!/usr/bin/env python3
"""
check_funding_extremes.py — Funding rate extreme detector.

Fetches current funding rates from Hyperliquid for tracked coins only.
Flags when rates exceed absolute threshold (>0.1% per 8h = extreme).

Uses absolute thresholds to avoid per-coin API calls (prevents 429 rate limits):
- >0.005 (0.5% per 8h) = critical
- >0.001 (0.1% per 8h) = high
- >0.0005 (0.05% per 8h) = medium

Usage:
    python3 check_funding_extremes.py          # check and print
    python3 check_funding_extremes.py --json   # JSON output only
"""
import json
import sys
import urllib.request
from datetime import datetime, timezone

# Absolute funding rate thresholds (per 8h period)
THRESHOLDS = {
    "critical": 0.005,   # 0.5% per 8h = 2.19% APR — very extreme
    "high": 0.001,       # 0.1% per 8h = 0.438% APR — elevated
    "medium": 0.0005,    # 0.05% per 8h = 0.219% APR — mildly elevated
}

COINS_TO_TRACK = [
    "BTC", "ETH", "SOL", "AVAX", "LINK", "DOGE", "ARB", "OP", "SUI",
    "AAVE", "ADA", "APT", "BCH", "BNB", "CRV", "DOT", "ENA",
    "FARTCOIN", "HYPE", "JUP", "LTC",
    "NEAR", "ONDO", "PAXG", "PUMP", "TRUMP", "TRX", "UNI", "WLD",
    "XPL", "XRP", "ZEC", "kBONK", "kPEPE", "kSHIB",
]


def fetch_hyperliquid_funding():
    """Fetch current funding rates for tracked coins from Hyperliquid."""
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
            return []
        universe = data[0].get("universe", []) if isinstance(data[0], dict) else []
        ctxs = data[1] if isinstance(data[1], list) else []
        
        rates = []
        for u, ctx in zip(universe, ctxs):
            if not isinstance(u, dict) or not isinstance(ctx, dict):
                continue
            coin = u.get("name", "")
            if coin not in COINS_TO_TRACK:
                continue
            funding = float(ctx.get("funding", 0))
            oi = float(ctx.get("openInterest", 0))
            mark = float(ctx.get("markPx", 0))
            rates.append({
                "coin": coin,
                "funding_rate": funding,
                "funding_pct_8h": funding * 100,
                "open_interest_usd": oi * mark,
                "mark_price": mark,
            })
        return rates
    except Exception as e:
        print(f"  [WARN] Hyperliquid funding fetch failed: {e}", file=sys.stderr)
        return []


def detect_extremes(rates_data):
    """Detect funding rates above absolute thresholds."""
    alerts = []
    for coin_data in rates_data:
        rate = coin_data["funding_rate"]
        abs_rate = abs(rate)
        
        severity = None
        for s, threshold in THRESHOLDS.items():
            if abs_rate >= threshold:
                severity = s
                break
        
        if not severity:
            continue
        
        # Positive funding = longs paying = long squeeze risk
        # Negative funding = shorts paying = short squeeze risk
        risk = "long_squeeze" if rate > 0 else "short_squeeze"
        action = "suppress_longs" if rate > 0 else "suppress_shorts"
        
        alerts.append({
            "coin": coin_data["coin"],
            "current_rate": rate,
            "current_pct_8h": rate * 100,
            "annualized_pct": rate * 3 * 365,  # 3 funding periods/day × 365
            "severity": severity,
            "risk": risk,
            "action": action,
            "open_interest_usd": coin_data["open_interest_usd"],
            "mark_price": coin_data["mark_price"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
    
    return alerts


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    
    rates = fetch_hyperliquid_funding()
    if not rates:
        print("[SILENT]")
        return
    
    alerts = detect_extremes(rates)
    
    if not alerts:
        print("[SILENT]")
        return
    
    # Sort by severity (critical first) then by absolute rate
    severity_order = {"critical": 0, "high": 1, "medium": 2}
    alerts.sort(key=lambda a: (severity_order.get(a["severity"], 3), -abs(a["current_rate"])))
    
    if args.json:
        print(json.dumps({"alerts": alerts}, indent=2))
    else:
        for a in alerts:
            print(f"ALERT|{a['coin']}|{a['risk']}|{a['current_pct_8h']:.4f}%|ann:{a['annualized_pct']:.1f}%|{a['severity']}|{a['action']}")


if __name__ == "__main__":
    main()