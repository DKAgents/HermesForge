#!/usr/bin/env python3
"""
liquidation_listener.py — Real-time market event listener daemon.

Runs as a systemd service. Monitors Hyperliquid for:
1. Liquidation cascade proxies (OI drop + sharp price move) — every 10 sec
2. Funding rate extremes — every 5 min
3. OI spikes — every 15 min

When any event is detected, fires an HTTP POST to a Hermes webhook endpoint.
Also logs all events to JSONL for historical analysis.

Usage:
    python3 liquidation_listener.py                    # run in foreground
    python3 liquidation_listener.py --webhook URL      # specify webhook URL
    python3 liquidation_listener.py --dry-run          # don't send webhooks
    python3 liquidation_listener.py --once             # single cycle test

systemd service: /etc/systemd/system/hermesforge-listener.service
"""
import json
import time
import sys
import os
import signal
import logging
import urllib.request
import urllib.error
import pathlib
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
POLL_INTERVAL_SEC = 10
FUNDING_CHECK_INTERVAL = 300
OI_CHECK_INTERVAL = 900
LIQ_OI_DROP_THRESHOLD = 0.05
LIQ_PRICE_MOVE_THRESHOLD = 0.015
FUNDING_CRITICAL = 0.005
FUNDING_HIGH = 0.001
FUNDING_MEDIUM = 0.0005
OI_SPIKE_THRESHOLD_PCT = 5.0

WEBHOOK_URL = os.environ.get(
    "HERMESFORGE_WEBHOOK_URL",
    "http://localhost:8644/webhooks/hermesforge-liq"
)
LOG_FILE = "/root/.hermes/logs/liquidation_listener.log"
EVENT_LOG_FILE = "/root/.hermes/market_data/liquidation_events.jsonl"

# --- Universe (single source of truth) ----------------------------------------
import pathlib as _pl
import sys as _sys
_sys.path.insert(0, str(_pl.Path(__file__).resolve().parent.parent))
from hermes_config.universe import COINS_TO_TRACK  # noqa: E402

_running = True
_prev_state = {}
_last_funding_check = 0
_last_oi_check = 0
_prev_oi = {}


def setup_logging():
    pathlib.Path(LOG_FILE).parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(LOG_FILE),
            logging.StreamHandler(sys.stderr),
        ]
    )


def signal_handler(signum, frame):
    global _running
    logging.info(f"Received signal {signum}, shutting down...")
    _running = False


def log_event(event):
    pathlib.Path(EVENT_LOG_FILE).parent.mkdir(parents=True, exist_ok=True)
    with open(EVENT_LOG_FILE, "a") as f:
        f.write(json.dumps(event, default=str) + "\n")


def fire_webhook(payload):
    data = json.dumps(payload, default=str).encode()
    try:
        req = urllib.request.Request(
            WEBHOOK_URL, data=data,
            headers={"Content-Type": "application/json", "User-Agent": "HermesForge-Listener/1.0"},
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            logging.info(f"Webhook sent (HTTP {resp.status}): {payload.get('event_type', '?')}")
            return True
    except Exception as e:
        logging.error(f"Webhook failed: {e}")
        return False


def fetch_hyperliquid_state():
    """Fetch current OI, price, funding for tracked coins."""
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
            }
        return state
    except Exception as e:
        logging.warning(f"Hyperliquid fetch failed: {e}")
        return {}


def check_liquidation_proxy(current, previous):
    """Detect liquidation cascades via OI drop + price move."""
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
        if oi_change < -LIQ_OI_DROP_THRESHOLD and abs(price_change) > LIQ_PRICE_MOVE_THRESHOLD:
            direction = "longs_liquidated" if price_change < 0 else "shorts_liquidated"
            severity = "critical" if abs(oi_change) > 0.15 else "high" if abs(oi_change) > 0.10 else "medium"
            alerts.append({
                "event_type": "liquidation_cascade",
                "coin": coin, "direction": direction,
                "oi_drop_pct": round(oi_change * 100, 2),
                "price_move_pct": round(price_change * 100, 2),
                "oi_lost_usd": abs(curr_oi - prev_oi),
                "funding_rate": curr.get("funding_rate", 0),
                "severity": severity,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
    return alerts


def check_funding_extremes(current):
    """Check for funding rate extremes."""
    global _last_funding_check
    now = time.time()
    if now - _last_funding_check < FUNDING_CHECK_INTERVAL:
        return []
    _last_funding_check = now
    
    alerts = []
    for coin, data in current.items():
        rate = data.get("funding_rate", 0)
        abs_rate = abs(rate)
        severity = None
        if abs_rate >= FUNDING_CRITICAL:
            severity = "critical"
        elif abs_rate >= FUNDING_HIGH:
            severity = "high"
        elif abs_rate >= FUNDING_MEDIUM:
            severity = "medium"
        if severity:
            risk = "long_squeeze" if rate > 0 else "short_squeeze"
            action = "suppress_longs" if rate > 0 else "suppress_shorts"
            alerts.append({
                "event_type": "funding_extreme",
                "coin": coin,
                "funding_rate": rate,
                "funding_pct_8h": rate * 100,
                "risk": risk, "action": action,
                "severity": severity,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
    return alerts


def check_oi_spikes(current):
    """Check for OI spikes by comparing to previous snapshot."""
    global _last_oi_check, _prev_oi
    now = time.time()
    if now - _last_oi_check < OI_CHECK_INTERVAL:
        return []
    _last_oi_check = now
    
    spikes = []
    if _prev_oi:
        for coin, curr_usd in current.items():
            prev_usd = _prev_oi.get(coin, {}).get("oi_usd", 0)
            if prev_usd == 0:
                continue
            pct = ((curr_usd.get("oi_usd", 0) - prev_usd) / prev_usd) * 100
            if abs(pct) >= OI_SPIKE_THRESHOLD_PCT:
                spikes.append({
                    "event_type": "oi_spike",
                    "coin": coin,
                    "direction": "increase" if pct > 0 else "decrease",
                    "pct_change": round(pct, 2),
                    "interpretation": "new_money" if pct > 0 else "unwinding",
                    "severity": "high" if abs(pct) > 10 else "medium",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })
    
    _prev_oi = {k: {"oi_usd": v.get("oi_usd", 0)} for k, v in current.items()}
    return spikes


def run(dry_run=False):
    global _prev_state
    logging.info(f"Listener started (webhook: {WEBHOOK_URL}, dry_run: {dry_run})")
    logging.info(f"Poll: {POLL_INTERVAL_SEC}s, Funding: {FUNDING_CHECK_INTERVAL}s, OI: {OI_CHECK_INTERVAL}s")
    
    # Initialize state with first fetch
    _prev_state = fetch_hyperliquid_state()
    logging.info(f"Initial state: {len(_prev_state)} coins loaded")
    
    while _running:
        try:
            current = fetch_hyperliquid_state()
            if not current:
                time.sleep(POLL_INTERVAL_SEC)
                continue
            
            # 1. Liquidation proxy (every poll)
            liq_alerts = check_liquidation_proxy(current, _prev_state)
            for a in liq_alerts:
                log_event(a)
                logging.warning(f"LIQUIDATION: {a['coin']} {a['direction']} OI:{a['oi_drop_pct']}% PX:{a['price_move_pct']}% [{a['severity']}]")
                if not dry_run:
                    fire_webhook(a)
            
            # 2. Funding extremes (every 5 min)
            fund_alerts = check_funding_extremes(current)
            for a in fund_alerts:
                log_event(a)
                logging.warning(f"FUNDING: {a['coin']} {a['funding_pct_8h']:.4f}% [{a['risk']}] [{a['severity']}]")
                if not dry_run:
                    fire_webhook(a)
            
            # 3. OI spikes (every 15 min)
            oi_spikes = check_oi_spikes(current)
            for s in oi_spikes:
                log_event(s)
                logging.warning(f"OI SPIKE: {s['coin']} {s['pct_change']:+.1f}% [{s['interpretation']}] [{s['severity']}]")
                if not dry_run:
                    fire_webhook(s)
            
            # Update state for next cycle
            _prev_state = current
            
        except Exception as e:
            logging.error(f"Main loop error: {e}", exc_info=True)
        
        for _ in range(POLL_INTERVAL_SEC):
            if not _running:
                break
            time.sleep(1)
    
    logging.info("Listener stopped.")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="HermesForge Market Event Listener")
    parser.add_argument("--webhook", default=None, help="Webhook URL override")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--once", action="store_true", help="Single cycle test")
    args = parser.parse_args()
    
    global WEBHOOK_URL
    if args.webhook:
        WEBHOOK_URL = args.webhook
    
    setup_logging()
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    if args.once:
        current = fetch_hyperliquid_state()
        if not current:
            print("[SILENT] — no data")
            return
        prev = _prev_state or {}
        all_alerts = []
        all_alerts.extend(check_liquidation_proxy(current, prev))
        all_alerts.extend(check_funding_extremes(current))
        all_alerts.extend(check_oi_spikes(current))
        if all_alerts:
            for a in all_alerts:
                print(json.dumps(a, indent=2, default=str))
                log_event(a)
                if not args.dry_run:
                    fire_webhook(a)
        else:
            print("[SILENT] — no events detected")
    else:
        run(dry_run=args.dry_run)


if __name__ == "__main__":
    main()