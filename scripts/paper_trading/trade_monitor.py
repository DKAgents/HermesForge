#!/usr/bin/env python3
"""
trade_monitor.py — HermesForge Trade Lifecycle Monitor

Checks all open paper trades against latest price data and posts Discord
alerts when trade events occur:
  - ENTRY:   pending trade's entry price has been reached
  - STOP:    entered trade's stop loss has been triggered
  - TARGET:  entered trade's take profit has been hit
  - TIME:    entered trade's time stop has expired

Each alert includes the terse trade ID as a Markdown hyperlink back to the
original setup embed.

Usage:
    python3 trade_monitor.py --dry-run       # show what would be posted
    python3 trade_monitor.py                 # post alerts to Discord
    python3 trade_monitor.py --crypto-only   # monitor crypto trades only
    python3 trade_monitor.py --stocks-only   # monitor stock trades only
"""

import sys
import os
import json
import argparse
import pathlib
import datetime
import subprocess
import pandas as pd

REPO_ROOT = pathlib.Path(__file__).parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "paper_trading"))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "discord"))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "validation"))

import trade_log
from trade_id import make_discord_url, make_discord_link

# ── Config ────────────────────────────────────────────────────────────────────

DISCORD_BOT_TOKEN = os.environ.get("DISCORD_BOT_TOKEN", "")
API_BASE = "https://discord.com/api/v10"

MARKET_DATA_DIR = pathlib.Path.home() / ".hermes" / "market_data"
CRYPTO_DATA_DIR = pathlib.Path.home() / ".hermes" / "market_data" / "crypto"

# Time stop: max bars to hold a trade (by strategy)
MAX_BARS_HELD = {
    "STR-A-ma-pullback-fibonacci": 8,
    "STR-B-macd-histogram-divergence": 8,
    "STR-D-sr-role-reversal": 8,
    "STR-I-adaptive-trend": 120,  # 120 bars per scanner code
    "STR-L-atr-contraction": 20,
    "STR-P-crosssectional": 21,  # monthly rebalance cycle
}


# ── Price data loading ───────────────────────────────────────────────────────

def _load_bars_since(ticker: str, entry_date: str, asset_class: str = "stock") -> pd.DataFrame:
    """Load cached OHLC bars for ticker strictly after entry_date."""
    data_dir = CRYPTO_DATA_DIR if asset_class == "crypto" else MARKET_DATA_DIR
    path = data_dir / f"{ticker}.parquet"
    if not path.exists():
        raise FileNotFoundError(f"No cached data for {ticker} ({asset_class})")
    df = pd.read_parquet(path)
    df.index = pd.to_datetime(df.index)
    df = df.sort_index()
    entry_ts = pd.to_datetime(entry_date)
    return df[df.index > entry_ts]


def _fetch_latest_crypto_price(ticker: str) -> dict | None:
    """Fetch the latest price bar from Hyperliquid API for real-time crypto monitoring."""
    try:
        import subprocess
        result = subprocess.run(
            ["curl", "-s", "-X", "POST", "https://api.hyperliquid.xyz/info",
             "-H", "Content-Type: application/json",
             "-d", json.dumps({"type": "candleSnapshot",
                               "req": {"coin": ticker, "interval": "1h",
                                       "startTime": int(
                                           (datetime.datetime.utcnow() -
                                            datetime.timedelta(hours=24)).timestamp() * 1000),
                                       "endTime": int(datetime.datetime.utcnow().timestamp() * 1000)}})],
            capture_output=True, text=True, timeout=15,
        )
        data = json.loads(result.stdout)
        if data and len(data) > 0:
            latest = data[-1]
            # Hyperliquid candle: [t, o, h, l, c, v]
            return {
                "open": float(latest[1]),
                "high": float(latest[2]),
                "low": float(latest[3]),
                "close": float(latest[4]),
                "volume": float(latest[5]),
                "date": datetime.datetime.fromtimestamp(latest[0] / 1000),
            }
    except Exception as e:
        print(f"  ⚠️ Failed to fetch live price for {ticker}: {e}")
    return None


# ── Event detection ──────────────────────────────────────────────────────────

def check_entry(trade: dict, bars: pd.DataFrame) -> dict:
    """
    Check if a pending trade's entry price has been reached.

    For longs: entry triggers when bar's low <= entry_price (price fell to buy level)
               OR entry_price is within bar's range (market order filled)
    For shorts: entry triggers when bar's high >= entry_price (price rose to sell level)
                OR entry_price is within bar's range (market order filled)

    Returns: {entered: bool, entry_date: str, entry_bar: int} or {entered: False}
    """
    entry_price = float(trade["entry_price"])
    direction = trade["direction"]

    for offset, (bar_date, row) in enumerate(bars.iterrows(), start=1):
        high = float(row["high"])
        low = float(row["low"])

        # Entry is triggered if entry_price is within the bar's range
        if low <= entry_price <= high:
            return {
                "entered": True,
                "entry_date": str(bar_date)[:10],
                "entry_bar": offset,
                "entry_price": entry_price,
            }

        # For longs: also check if low dropped to entry (limit buy fill)
        if direction == "long" and low <= entry_price:
            return {
                "entered": True,
                "entry_date": str(bar_date)[:10],
                "entry_bar": offset,
                "entry_price": entry_price,
            }

        # For shorts: also check if high rose to entry (limit sell fill)
        if direction == "short" and high >= entry_price:
            return {
                "entered": True,
                "entry_date": str(bar_date)[:10],
                "entry_bar": offset,
                "entry_price": entry_price,
            }

    return {"entered": False}


def check_exit(trade: dict, bars: pd.DataFrame) -> dict:
    """
    Check if an entered trade has hit stop, target, or time stop.
    Reuses the same logic as track_outcomes.py: stop wins on tie.

    Returns: {action: 'closed'|'still_open', exit_reason, exit_price, exit_date, bars_held}
    """
    direction = trade["direction"]
    stop_price = float(trade["stop_price"])
    target_price = float(trade["target_price"])
    strategy_id = trade["strategy_id"]
    max_bars = MAX_BARS_HELD.get(strategy_id, 21)

    for offset, (bar_date, row) in enumerate(bars.iterrows(), start=1):
        high = float(row["high"])
        low = float(row["low"])

        # Check stop and target
        if direction == "long":
            target_hit = high >= target_price
            stop_hit = low <= stop_price
        else:  # short
            target_hit = low <= target_price
            stop_hit = high >= stop_price

        # Stop wins on tie (conservative)
        if stop_hit:
            return {
                "action": "closed", "exit_reason": "stop",
                "exit_price": stop_price, "exit_date": str(bar_date)[:10],
                "bars_held": offset,
            }
        if target_hit:
            return {
                "action": "closed", "exit_reason": "target",
                "exit_price": target_price, "exit_date": str(bar_date)[:10],
                "bars_held": offset,
            }

        # Time stop
        if offset >= max_bars:
            return {
                "action": "closed", "exit_reason": "time",
                "exit_price": float(row["close"]), "exit_date": str(bar_date)[:10],
                "bars_held": offset,
            }

    return {"action": "still_open", "reason": f"{len(bars)} bars checked, no hit yet"}


# ── Discord alert posting ─────────────────────────────────────────────────────

def _post_alert(channel_id: str, content: str, dry_run: bool = False) -> dict:
    """Post a brief alert message to a Discord channel."""
    if dry_run:
        print(f"  [dry-run] {content}")
        return {"status": "dry_run"}

    url = f"{API_BASE}/channels/{channel_id}/messages"
    cmd = [
        "curl", "-s", "-X", "POST",
        "-H", f"Authorization: Bot {DISCORD_BOT_TOKEN}",
        "-H", "Content-Type: application/json",
        "-d", json.dumps({"content": content}),
        url,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
    try:
        response = json.loads(result.stdout)
        if "id" in response:
            return {"status": "ok", "message_id": response["id"]}
        else:
            return {"status": "error", "response": result.stdout[:300]}
    except (json.JSONDecodeError, KeyError):
        return {"status": "error", "response": result.stdout[:300]}


def _format_alert(event_type: str, trade: dict, exit_info: dict = None) -> str:
    """
    Format a brief alert message with hyperlinked trade ID.

    Event types: ENTRY, STOP, TARGET, TIME
    """
    short_id = trade.get("short_id", "?")
    ticker = trade.get("ticker", "?")
    direction = trade.get("direction", "?").upper()
    channel_id = trade.get("discord_channel_id", "")
    message_id = trade.get("discord_message_id", "")

    # Build the hyperlink
    if channel_id and message_id:
        link = make_discord_link(short_id, channel_id, message_id)
    else:
        link = f"`{short_id}`"

    def _fmt_price(p):
        p = float(p)
        if abs(p) < 1.0:
            return f"${p:.6f}"
        elif abs(p) < 100.0:
            return f"${p:.4f}"
        else:
            return f"${p:,.2f}"

    if event_type == "ENTRY":
        entry_price = float(trade["entry_price"])
        return f"🟢 **ENTRY** | {link} | {ticker} {direction} entered at {_fmt_price(entry_price)}"

    elif event_type == "STOP":
        exit_price = exit_info["exit_price"]
        r_mult = _compute_r(trade, exit_price)
        return f"🛑 **STOP** | {link} | {ticker} {direction} stopped at {_fmt_price(exit_price)} ({r_mult:+.1f}R)"

    elif event_type == "TARGET":
        exit_price = exit_info["exit_price"]
        r_mult = _compute_r(trade, exit_price)
        return f"🎯 **TARGET** | {link} | {ticker} {direction} target hit at {_fmt_price(exit_price)} ({r_mult:+.1f}R)"

    elif event_type == "TIME":
        exit_price = exit_info["exit_price"]
        r_mult = _compute_r(trade, exit_price)
        bars = exit_info.get("bars_held", "?")
        return f"⏱️ **TIME STOP** | {link} | {ticker} {direction} time stop at {_fmt_price(exit_price)} ({r_mult:+.1f}R, {bars} bars)"

    return f"❓ **UNKNOWN** | {link} | {ticker} {direction}"


def _compute_r(trade: dict, exit_price: float) -> float:
    """Compute R-multiple for a trade at a given exit price."""
    entry = float(trade["entry_price"])
    stop = float(trade["stop_price"])
    risk = abs(entry - stop)
    if risk <= 0:
        return 0.0
    direction = trade.get("direction", "long")
    if direction == "long":
        return (exit_price - entry) / risk
    else:
        return (entry - exit_price) / risk


# ── Main monitor loop ────────────────────────────────────────────────────────

def run(dry_run: bool = False, crypto_only: bool = False, stocks_only: bool = False) -> dict:
    """
    Main monitor loop. Checks all open trades and posts alerts for events.

    Returns summary dict.
    """
    summary = {
        "pending_checked": 0,
        "entered": 0,
        "entered_checked": 0,
        "stopped": 0,
        "targeted": 0,
        "time_stopped": 0,
        "still_open": 0,
        "errors": 0,
        "alerts_posted": 0,
        "error_details": [],
    }

    # ── Check pending trades for entry ──────────────────────────────────────
    pending = trade_log.get_pending_trades()
    summary["pending_checked"] = len(pending)

    for trade in pending:
        asset_class = trade.get("asset_class", "stock")
        if crypto_only and asset_class != "crypto":
            continue
        if stocks_only and asset_class != "stock":
            continue

        short_id = trade.get("short_id", "?")
        ticker = trade["ticker"]

        try:
            bars = _load_bars_since(ticker, trade["entry_date"], asset_class)
        except FileNotFoundError as e:
            summary["errors"] += 1
            summary["error_details"].append(f"{short_id}: {e}")
            continue

        if bars.empty:
            continue

        entry_result = check_entry(trade, bars)

        if entry_result["entered"]:
            print(f"  🟢 ENTRY: {short_id} — {ticker} {trade['direction']} entered at ${float(trade['entry_price']):,.2f}")
            summary["entered"] += 1

            # Post alert
            alert = _format_alert("ENTRY", trade)
            channel_id = trade.get("discord_channel_id", "")
            if channel_id:
                result = _post_alert(channel_id, alert, dry_run)
                if result["status"] == "ok":
                    summary["alerts_posted"] += 1
                elif result["status"] == "error":
                    summary["errors"] += 1
                    summary["error_details"].append(f"{short_id} alert failed: {result.get('response', '')}")

            # Update trade status
            if not dry_run:
                trade_log.update_entry_status(trade["trade_id"], "entered")

    # ── Check entered trades for stop/target/time ────────────────────────────
    entered = trade_log.get_entered_trades()
    summary["entered_checked"] = len(entered)

    for trade in entered:
        asset_class = trade.get("asset_class", "stock")
        if crypto_only and asset_class != "crypto":
            continue
        if stocks_only and asset_class != "stock":
            continue

        short_id = trade.get("short_id", "?")
        ticker = trade["ticker"]

        try:
            bars = _load_bars_since(ticker, trade["entry_date"], asset_class)
        except FileNotFoundError as e:
            summary["errors"] += 1
            summary["error_details"].append(f"{short_id}: {e}")
            continue

        if bars.empty:
            continue

        exit_result = check_exit(trade, bars)

        if exit_result["action"] == "closed":
            reason = exit_result["exit_reason"]
            event_map = {"stop": "STOP", "target": "TARGET", "time": "TIME"}
            event_type = event_map.get(reason, "TIME")
            summary_key = {"stop": "stopped", "target": "targeted", "time": "time_stopped"}
            summary[summary_key.get(reason, "time_stopped")] += 1

            print(f"  {event_type}: {short_id} — {ticker} {trade['direction']} {reason} at ${exit_result['exit_price']:,.2f}")

            # Post alert
            alert = _format_alert(event_type, trade, exit_result)
            channel_id = trade.get("discord_channel_id", "")
            if channel_id:
                result = _post_alert(channel_id, alert, dry_run)
                if result["status"] == "ok":
                    summary["alerts_posted"] += 1
                elif result["status"] == "error":
                    summary["errors"] += 1
                    summary["error_details"].append(f"{short_id} alert failed: {result.get('response', '')}")

            # Close the trade
            if not dry_run:
                trade_log.close_trade(
                    trade["trade_id"],
                    exit_result["exit_date"],
                    exit_result["exit_price"],
                    exit_result["exit_reason"],
                    bars_held=exit_result["bars_held"],
                )
        else:
            summary["still_open"] += 1

    return summary


def main():
    ap = argparse.ArgumentParser(description="HermesForge Trade Lifecycle Monitor")
    ap.add_argument("--dry-run", action="store_true", help="Show what would be posted without posting")
    ap.add_argument("--crypto-only", action="store_true")
    ap.add_argument("--stocks-only", action="store_true")
    args = ap.parse_args()

    print(f"\n{'='*60}")
    print(f"HermesForge Trade Monitor — {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"{'='*60}")

    summary = run(dry_run=args.dry_run,
                  crypto_only=args.crypto_only,
                  stocks_only=args.stocks_only)

    print(f"\n{'='*60}")
    print(f"SUMMARY:")
    print(f"  Pending trades checked: {summary['pending_checked']}")
    print(f"  Entries triggered:     {summary['entered']}")
    print(f"  Entered trades checked: {summary['entered_checked']}")
    print(f"  Stop losses hit:      {summary['stopped']}")
    print(f"  Targets hit:           {summary['targeted']}")
    print(f"  Time stops:            {summary['time_stopped']}")
    print(f"  Still open:            {summary['still_open']}")
    print(f"  Alerts posted:        {summary['alerts_posted']}")
    print(f"  Errors:               {summary['errors']}")
    for e in summary["error_details"]:
        print(f"    ERROR: {e}")


if __name__ == "__main__":
    main()
