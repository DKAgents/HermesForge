#!/usr/bin/env python3
"""
strategy_status.py — HermesForge Strategy Dashboard

Posts a comprehensive status overview of all trading strategies to a Discord
channel. On each run, deletes the previous dashboard message and posts a new
one. If the channel is an announcement channel, crossposts the new message.

Strategy data is compiled from the scanner files and regime detector.

Usage:
    python3 strategy_status.py                    # post + crosspost
    python3 strategy_status.py --dry-run          # format only, no posting
    python3 strategy_status.py --channel-id <id>  # override channel
"""

import os
import sys
import json
import subprocess
import pathlib
import datetime
import time

sys.path.insert(0, str(pathlib.Path(__file__).parent))

DISCORD_BOT_TOKEN = os.environ.get("DISCORD_BOT_TOKEN", "")
API_BASE = "https://discord.com/api/v10"

# Channel ID for #strategy-status (set via env or hardcode after channel creation)
CHANNEL_ID = os.environ.get("STRATEGY_STATUS_CHANNEL_ID", "")

# File to track the previous message ID for delete-and-replace
STATE_FILE = pathlib.Path.home() / ".hermes" / "strategy_status_state.json"

# ── Strategy definitions ────────────────────────────────────────────────────

STRATEGIES = [
    {
        "id": "STR-A",
        "name": "MA Pullback + Fibonacci",
        "status": "KILLED",
        "description": "Pullback to MA50 within an established trend, entering at Fibonacci 38-62% retracement zone. Targets via Fib extensions (127.2%, 161.8%).",
        "regimes": ["trending"],
        "edge": "Mean reversion within trend",
    },
    {
        "id": "STR-B",
        "name": "MACD Histogram Divergence",
        "status": "LIVE",
        "description": "Price makes new swing high but MACD makes lower high (bearish) or vice versa (bullish). Entry on MACD line/signal cross. Requires 15+ bar maturity gate. ATR-based stop.",
        "regimes": ["trending", "ranging"],
        "edge": "Momentum exhaustion reversal",
    },
    {
        "id": "STR-C",
        "name": "Breakout + Volume",
        "status": "KILLED",
        "description": "Price breaks above 20-bar high with volume confirmation (1.5x+ average). Prior high becomes new support. Role reversal for stop placement.",
        "regimes": ["trending"],
        "edge": "Range breakout with volume confirmation",
    },
    {
        "id": "STR-D",
        "name": "S/R Role Reversal",
        "status": "KILLED",
        "description": "Prior resistance tested as new support. Two-bar reclaim confirms. Walk-forward: NO EDGE (p=0.435, OOS R=0.033). Phase 1A edge (0.227R) didn't survive costs.",
        "regimes": ["trending", "ranging", "transitional", "high-vol", "low-vol"],
        "edge": "Structural level role reversal (FAILED walk-forward)",
    },
    {
        "id": "STR-E",
        "name": "RSI Mean Reversion",
        "status": "KILLED",
        "description": "RSI extremes (< 30 or > 70) as mean-reversion entry signals. Counter-trend trades expecting return to RSI 50.",
        "regimes": ["ranging"],
        "edge": "RSI extreme mean reversion",
    },
    {
        "id": "STR-F",
        "name": "Bollinger Squeeze",
        "status": "KILLED",
        "description": "Bollinger Band squeeze (low volatility) followed by expansion breakout. Direction determined by candle close outside bands.",
        "regimes": ["low-volatility"],
        "edge": "Volatility expansion breakout",
    },
    {
        "id": "STR-G",
        "name": "Relative Strength / Sector Rotation",
        "status": "KILLED",
        "description": "Cross-sectional relative strength ranking. Long strongest sectors, short weakest. Momentum-based sector rotation.",
        "regimes": ["trending"],
        "edge": "Sector rotation momentum",
    },
    {
        "id": "STR-H",
        "name": "First Pullback Trend Swing",
        "status": "KILLED",
        "description": "High-RR first pullback in an established trend. Swing-segmented leg definition (v1.4). Entry on pullback to key level.",
        "regimes": ["trending"],
        "edge": "First pullback in trend = highest RR entry",
    },
    {
        "id": "STR-I",
        "name": "AdaptiveTrend (Momentum + ATR Trailing Stop)",
        "status": "LIVE",
        "description": "Momentum (10-bar) exceeds +/-20% threshold with SMA200 trend filter. ATR(14) trailing stop at 2.0x ratchets with trend. 120-bar time stop. RESTRICTED to stocks (killed on crypto: Sharpe 0.151 per ADR-004 Amendment 1).",
        "regimes": ["trending"],
        "edge": "Adaptive trend-following with ratcheting stop (stocks only)",
    },
    {
        "id": "STR-J",
        "name": "EUFEARIA CCI Reversal",
        "status": "KILLED",
        "description": "CCI (Commodity Channel Index) reversal signals. Based on EUFEARIA PRO 7 Pine Script by Philip Paul. Multi-oscillator confirmation.",
        "regimes": ["ranging"],
        "edge": "CCI extreme reversal",
    },
    {
        "id": "STR-K",
        "name": "Breadth Gap",
        "status": "KILLED",
        "description": "Market breadth gap analysis. Uses advance/decline ratios to identify extreme breadth conditions for reversal entries.",
        "regimes": ["transitional"],
        "edge": "Breadth extreme reversal",
    },
    {
        "id": "STR-L",
        "name": "ATR Contraction",
        "status": "WATCH",
        "description": "ATR contraction pattern identifying volatility compression before expansion. Low-volatility regime entry. Insufficient signals for walk-forward (6 in 7 years).",
        "regimes": ["low-volatility"],
        "edge": "Volatility compression → expansion",
    },
    {
        "id": "STR-M",
        "name": "Selling Climax",
        "status": "KILLED",
        "description": "Selling climax detection — high-volume capitulation bars marking potential reversal points. Counter-trend entry after extreme selling.",
        "regimes": ["high-volatility"],
        "edge": "Capitulation reversal",
    },
    {
        "id": "STR-N",
        "name": "Outside Day Reversal",
        "status": "KILLED",
        "description": "Outside day candlestick pattern (engulfing) as reversal signal. Two-bar pattern where current bar engulfs prior bar's range.",
        "regimes": ["transitional"],
        "edge": "Candlestick engulfing reversal",
    },
    {
        "id": "STR-O",
        "name": "Price Momentum Factor",
        "status": "KILLED",
        "description": "Crypto-optimized price momentum factor strategy. Price relative to SMA200 as momentum signal. Single-factor approach.",
        "regimes": ["trending", "ranging"],
        "edge": "Single-factor price momentum",
    },
    {
        "id": "STR-P",
        "name": "Cross-Sectional Factor Ranking",
        "status": "WATCH",
        "description": "Multi-factor cross-sectional ranking combining MOM12_1 (12-month momentum, 0.33 weight), LIQUID (dollar volume, 0.33), PRICEMOM (price vs SMA200, 0.34). Walk-forward: ROBUST EDGE (p=0.03, OOS R=0.12, 4/5 windows positive). Edge is thin but statistically significant.",
        "regimes": ["ranging", "trending"],
        "edge": "Multi-factor cross-sectional (crypto only, walk-forward validated)",
    },
]

# ── Status formatting ────────────────────────────────────────────────────────

STATUS_EMOJI = {
    "LIVE": "🟢",
    "WATCH": "🟡",
    "KILLED": "🔴",
}

STATUS_COLOR = {
    "LIVE": 0x3fb950,     # green
    "WATCH": 0xe3b341,    # yellow/gold
    "KILLED": 0xf85149,   # red
}


def format_strategy_dashboard() -> dict:
    """Format the strategy status dashboard as a Discord embed."""
    dt = datetime.datetime.utcnow()

    live = [s for s in STRATEGIES if s["status"] == "LIVE"]
    watch = [s for s in STRATEGIES if s["status"] == "WATCH"]
    killed = [s for s in STRATEGIES if s["status"] == "KILLED"]

    # Build fields — one per strategy, grouped by status
    fields = []

    # Live strategies
    if live:
        lines = []
        for s in live:
            lines.append(f"{STATUS_EMOJI[s['status']]} **{s['id']} — {s['name']}**")
            lines.append(f"  {s['description']}")
            lines.append(f"  Regimes: {', '.join(s['regimes'])} | Edge: {s['edge']}")
            lines.append("")
        fields.append({
            "name": f"🟢 LIVE ({len(live)})",
            "value": "\n".join(lines).strip(),
            "inline": False,
        })

    # Watch strategies
    if watch:
        lines = []
        for s in watch:
            lines.append(f"{STATUS_EMOJI[s['status']]} **{s['id']} — {s['name']}**")
            lines.append(f"  {s['description']}")
            lines.append(f"  Regimes: {', '.join(s['regimes'])} | Edge: {s['edge']}")
            lines.append("")
        fields.append({
            "name": f"🟡 WATCH ({len(watch)})",
            "value": "\n".join(lines).strip(),
            "inline": False,
        })

    # Killed strategies (compact)
    if killed:
        lines = []
        for s in killed:
            lines.append(f"{STATUS_EMOJI[s['status']]} **{s['id']}** — {s['name']}")
        fields.append({
            "name": f"🔴 KILLED ({len(killed)})",
            "value": "\n".join(lines),
            "inline": False,
        })

    embed = {
        "title": "📊 HermesForge Strategy Dashboard",
        "description": (
            f"**{len(STRATEGIES)} strategies tested** | "
            f"🟢 {len(live)} live | 🟡 {len(watch)} watch | 🔴 {len(killed)} killed\n"
            f"Last updated: {dt.strftime('%Y-%m-%d %H:%M')} UTC"
        ),
        "color": 0x58a6ff,
        "fields": fields,
        "footer": {"text": "HermesForge Strategy Pipeline"},
        "timestamp": dt.isoformat() + "Z",
    }

    return embed


# ── Discord API helpers ─────────────────────────────────────────────────────

def _api_request(method: str, url: str, data: dict = None) -> dict:
    """Make a Discord API request."""
    cmd = [
        "curl", "-s", "-X", method,
        "-H", f"Authorization: Bot {DISCORD_BOT_TOKEN}",
    ]
    if data:
        cmd += ["-H", "Content-Type: application/json", "-d", json.dumps(data)]
    cmd += [url]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    try:
        return json.loads(result.stdout)
    except (json.JSONDecodeError, ValueError):
        return {"error": result.stdout[:500]}


def _delete_message(channel_id: str, message_id: str) -> dict:
    """Delete a message from a channel."""
    return _api_request(
        "DELETE",
        f"{API_BASE}/channels/{channel_id}/messages/{message_id}",
    )


def _crosspost_message(channel_id: str, message_id: str) -> dict:
    """Crosspost (publish) a message from an announcement channel."""
    return _api_request(
        "POST",
        f"{API_BASE}/channels/{channel_id}/messages/{message_id}/crosspost",
    )


def _load_state() -> dict:
    """Load the previous message state."""
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {}


def _save_state(state: dict) -> None:
    """Save the message state."""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2))


def post_strategy_dashboard(channel_id: str, dry_run: bool = False) -> dict:
    """
    Post the strategy dashboard to a channel, replacing the previous post.

    1. Load previous message ID from state file
    2. Delete the previous message (if it exists)
    3. Post the new dashboard embed
    4. If announcement channel, crosspost the new message
    5. Save the new message ID to state file
    """
    if not channel_id:
        return {"error": "No channel ID provided. Set STRATEGY_STATUS_CHANNEL_ID env var."}

    embed = format_strategy_dashboard()

    if dry_run:
        print("=== DRY RUN ===")
        print(json.dumps(embed, indent=2))
        return {"status": "dry_run", "embed": embed}

    # 1. Load previous state
    state = _load_state()
    prev_msg_id = state.get(channel_id, {}).get("message_id")

    # 2. Delete previous message
    if prev_msg_id:
        print(f"  Deleting previous dashboard (msg {prev_msg_id})...")
        del_result = _delete_message(channel_id, prev_msg_id)
        if "id" in del_result or del_result.get("code") == 10008:
            # 10008 = Unknown Message (already deleted)
            print(f"  ✅ Previous message deleted (or already gone)")
        else:
            print(f"  ⚠️ Delete result: {del_result}")
        time.sleep(1)

    # 3. Post new dashboard
    payload = {"embeds": [embed]}
    post_result = _api_request(
        "POST",
        f"{API_BASE}/channels/{channel_id}/messages",
        payload,
    )

    if "id" not in post_result:
        return {"error": "Failed to post dashboard", "response": post_result}

    new_msg_id = post_result["id"]
    print(f"  ✅ Dashboard posted (msg {new_msg_id})")

    # 4. Try to crosspost (works if announcement channel, fails silently if not)
    time.sleep(1)
    crosspost_result = _crosspost_message(channel_id, new_msg_id)
    if "id" in crosspost_result:
        print(f"  ✅ Crossposted to followers")
    else:
        print(f"  ℹ️ Not crossposted (not an announcement channel or no followers)")

    # 5. Save state
    state[channel_id] = {
        "message_id": new_msg_id,
        "posted_at": datetime.datetime.utcnow().isoformat() + "Z",
    }
    _save_state(state)

    return {"status": "ok", "message_id": new_msg_id}


# ── CLI ──────────────────────────────────────────────────────────────────────

def main():
    import argparse
    ap = argparse.ArgumentParser(description="HermesForge Strategy Dashboard")
    ap.add_argument("--dry-run", action="store_true", help="Format only, no posting")
    ap.add_argument("--channel-id", type=str, default=None,
                    help="Override channel ID (default: STRATEGY_STATUS_CHANNEL_ID env)")
    args = ap.parse_args()

    channel_id = args.channel_id or CHANNEL_ID
    if not channel_id:
        print("ERROR: No channel ID. Set STRATEGY_STATUS_CHANNEL_ID env var or use --channel-id")
        sys.exit(1)

    result = post_strategy_dashboard(channel_id, dry_run=args.dry_run)
    if "error" in result:
        print(f"ERROR: {result['error']}")
        sys.exit(1)
    print("Done.")


if __name__ == "__main__":
    main()
