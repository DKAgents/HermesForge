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
import glob

sys.path.insert(0, str(pathlib.Path(__file__).parent))

DISCORD_BOT_TOKEN = os.environ.get("DISCORD_BOT_TOKEN", "")
API_BASE = "https://discord.com/api/v10"

# Channel ID for #strategy-status (set via env or hardcode after channel creation)
CHANNEL_ID = os.environ.get("STRATEGY_STATUS_CHANNEL_ID", "")

# File to track the previous message ID for delete-and-replace
STATE_FILE = pathlib.Path.home() / ".hermes" / "strategy_status_state.json"

# Path to research pipeline JSON output
REPO_ROOT = pathlib.Path(__file__).parent.parent.parent
RESEARCH_DATA_DIR = REPO_ROOT / "data"

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
    {
        "id": "STR-Q",
        "name": "Liquidity Sweep Reversal",
        "status": "LIVE",
        "description": "Institutional stop-loss sweep detection on 5m intraday bars. Enters AFTER price sweeps a liquidity level (PDH/PDL, equal highs/lows, round numbers) and reverses. Stop behind sweep wick, 3R target. Phase 1B PASS: OOS +1.131R, 62.1% WR, p=0.0000. Deep backtest: 826 trades, +0.588R, 2.18 PF. Runs every 5 min via cron b9fb0afb1e29.",
        "regimes": ["all"],
        "edge": "Post-sweep reversal entry (intraday)",
    },
    {
        "id": "STR-R",
        "name": "Williams Alligator Trend",
        "status": "LIVE",
        "description": "Bill Williams' Alligator indicator — three SMMA lines (Jaw 13/8, Teeth 8/5, Lips 5/3) that detect trend awakening. Enters when lines fan out from a sleeping state, exits when they tangle again. Phase 1A: Stocks 510 trades, 35.7% WR, +0.242R, PF 1.44. Crypto: 280 trades, 29.3% WR, +0.172R, PF 1.30. Long-only on stocks, bidirectional on crypto.",
        "regimes": ["trending"],
        "edge": "Trend awakening detection via SMMA fan",
    },
]

# ── Research Pipeline Strategies ──────────────────────────────────────────────

def _load_latest_research() -> dict:
    """Load the most recent research pipeline JSON output."""
    pattern = str(RESEARCH_DATA_DIR / "research-*.json")
    files = sorted(glob.glob(pattern))
    if not files:
        return {}
    with open(files[-1]) as f:
        return json.load(f)


def _build_research_strategies() -> list:
    """
    Build strategy entries from the latest research pipeline run.
    Returns list of strategy dicts matching the manual strategy format.
    """
    research = _load_latest_research()
    if not research:
        return []

    strategies = []
    ts = research.get("timestamp", "unknown")[:10]

    # Factor screener candidates
    fs = research.get("factor_screener", {})
    for asset_key, asset_label in [("stock", "Stocks"), ("crypto", "Crypto")]:
        asset_data = fs.get(asset_key, {})
        for cand in asset_data.get("candidates", []):
            factor = cand.get("factor", "?")
            sharpe = cand.get("sharpe", 0)
            p_val = cand.get("p_value", 1)
            ann_ret = cand.get("annualized_return", 0)
            direction = "inverted" if sharpe < 0 else "normal"
            strategies.append({
                "id": f"RP-F-{factor}",
                "name": f"Factor: {factor} ({asset_label})",
                "status": "CANDIDATE",
                "description": f"Factor screener candidate. Sharpe {sharpe:.3f}, p={p_val:.4f}, annual return {ann_ret*100:.1f}%. Direction: {direction}. Discovered {ts}.",
                "regimes": ["various"],
                "edge": f"Factor anomaly ({direction})",
            })

    # Revival candidates
    rt = research.get("revival_tester", {})
    for cand in rt.get("candidates", []):
        strat = cand.get("strategy", "?")
        name = cand.get("name", "?")
        mean_r = cand.get("mean_r", 0)
        p_val = cand.get("p_value", 1)
        n_sig = cand.get("n_signals", 0)
        hit_rate = cand.get("hit_rate", 0)
        strategies.append({
            "id": f"RP-R-{strat.replace('STR-','')}",
            "name": f"Revival: {name}",
            "status": "CANDIDATE",
            "description": f"Killed strategy showing revival. Mean R={mean_r:.4f}, p={p_val:.4f}, {n_sig} signals, {hit_rate*100:.0f}% hit rate. Discovered {ts}.",
            "regimes": ["various"],
            "edge": "Revival candidate — needs full walk-forward",
        })

    # Hypothesis candidates
    hg = research.get("hypothesis_generator", {})
    for asset_key, asset_label in [("stock", "Stocks"), ("crypto", "Crypto")]:
        asset_data = hg.get(asset_key, {})
        for cand in asset_data.get("candidates", []):
            hyp = cand.get("hypothesis", "?")
            sharpe = cand.get("sharpe", 0)
            p_val = cand.get("p_value", 1)
            desc = cand.get("description", "")
            strategies.append({
                "id": f"RP-H-{asset_key[:3]}",
                "name": f"Hypothesis: {hyp}",
                "status": "CANDIDATE",
                "description": f"Factor combination hypothesis. Sharpe {sharpe:.3f}, p={p_val:.4f}. {desc}. Discovered {ts}.",
                "regimes": ["various"],
                "edge": "Factor combination candidate",
            })

    return strategies


# ── Status formatting ────────────────────────────────────────────────────────

STATUS_EMOJI = {
    "LIVE": "🟢",
    "WATCH": "🟡",
    "KILLED": "🔴",
    "CANDIDATE": "🔬",
}

STATUS_COLOR = {
    "LIVE": 0x3fb950,     # green
    "WATCH": 0xe3b341,    # yellow/gold
    "KILLED": 0xf85149,   # red
    "CANDIDATE": 0xa371f7, # purple
}


def _format_group(strategies: list, status: str, label: str) -> dict | None:
    """Format a group of strategies into an embed field."""
    group = [s for s in strategies if s["status"] == status]
    if not group:
        return None

    lines = []
    if status == "KILLED":
        # Compact format for killed strategies
        for s in group:
            lines.append(f"{STATUS_EMOJI[s['status']]} **{s['id']}** — {s['name']}")
    elif status == "CANDIDATE":
        # Semi-compact for research candidates — one line each with key stats
        for s in group:
            lines.append(f"{STATUS_EMOJI[s['status']]} **{s['id']}** — {s['name']}")
            lines.append(f"  {s['description'][:120]}")
    else:
        for s in group:
            lines.append(f"{STATUS_EMOJI[s['status']]} **{s['id']} — {s['name']}**")
            lines.append(f"  {s['description']}")
            lines.append(f"  Regimes: {', '.join(s['regimes'])} | Edge: {s['edge']}")
            lines.append("")

    emoji = STATUS_EMOJI[status]
    return {
        "name": f"{emoji} {label} ({len(group)})",
        "value": "\n".join(lines).strip(),
        "inline": False,
    }


def format_strategy_dashboard() -> dict:
    """Format the strategy status dashboard as a Discord embed."""
    dt = datetime.datetime.utcnow()

    # Load research pipeline strategies
    research_strategies = _build_research_strategies()

    # Manual strategies
    manual = STRATEGIES
    manual_live = [s for s in manual if s["status"] == "LIVE"]
    manual_watch = [s for s in manual if s["status"] == "WATCH"]
    manual_killed = [s for s in manual if s["status"] == "KILLED"]

    # Research strategies
    research_candidates = [s for s in research_strategies if s["status"] == "CANDIDATE"]

    total_strategies = len(manual) + len(research_strategies)

    fields = []

    # ── Manually Defined Strategies ──
    fields.append({
        "name": "━━━━━━━━━━━━━━━━━━━━━━━",
        "value": "**Manual Strategies** (hand-designed and validated)",
        "inline": False,
    })

    for status, label in [("LIVE", "LIVE"), ("WATCH", "WATCH"), ("KILLED", "KILLED")]:
        field = _format_group(manual, status, label)
        if field:
            fields.append(field)

    # ── Research Pipeline Strategies ──
    if research_strategies:
        fields.append({
            "name": "━━━━━━━━━━━━━━━━━━━━━━━",
            "value": "**Research Pipeline** (discovered by automated weekly scans)",
            "inline": False,
        })
        # Split candidates into chunks to stay under Discord 1024-char field limit
        candidate_lines = []
        for s in research_strategies:
            candidate_lines.append(f"🔬 **{s['id']}** — {s['name']}")
            candidate_lines.append(f"  {s['description'][:100]}")

        # Chunk into fields of ~900 chars to stay safe
        current_chunk = []
        current_len = 0
        chunk_num = 1
        for line in candidate_lines:
            if current_len + len(line) + 1 > 900 and current_chunk:
                fields.append({
                    "name": f"🔬 CANDIDATE ({len(research_candidates)})" if chunk_num == 1 else f"🔬 CANDIDATE (cont.)",
                    "value": "\n".join(current_chunk).strip(),
                    "inline": False,
                })
                current_chunk = []
                current_len = 0
                chunk_num += 1
            current_chunk.append(line)
            current_len += len(line) + 1
        if current_chunk:
            fields.append({
                "name": f"🔬 CANDIDATE ({len(research_candidates)})" if chunk_num == 1 else "🔬 CANDIDATE (cont.)",
                "value": "\n".join(current_chunk).strip(),
                "inline": False,
            })

    embed = {
        "title": "📊 HermesForge Strategy Dashboard",
        "description": (
            f"**{total_strategies} strategies** ({len(manual)} manual + {len(research_strategies)} research) | "
            f"🟢 {len(manual_live)} live | 🟡 {len(manual_watch)} watch | "
            f"🔴 {len(manual_killed)} killed | 🔬 {len(research_candidates)} candidates\n"
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


def _get_all_messages(channel_id: str) -> list:
    """Fetch all bot messages from the channel (up to 100)."""
    url = f"{API_BASE}/channels/{channel_id}/messages?limit=100"
    result = _api_request("GET", url)
    if isinstance(result, list):
        return result
    return []


def _delete_all_bot_messages(channel_id: str) -> int:
    """Delete all messages posted by the bot in the channel. Returns count deleted."""
    messages = _get_all_messages(channel_id)
    bot_id = None
    deleted = 0
    for msg in messages:
        author = msg.get("author", {})
        # Only delete messages from our bot
        if author.get("bot") and author.get("username", "").startswith("Trading Swarm"):
            msg_id = msg.get("id")
            if msg_id:
                _delete_message(channel_id, msg_id)
                deleted += 1
                time.sleep(0.6)  # Rate limit safety (5 deletes per 3 seconds)
    return deleted


def post_strategy_dashboard(channel_id: str, dry_run: bool = False) -> dict:
    """
    Post the strategy dashboard to a channel, replacing ALL previous posts.

    1. Delete ALL previous bot messages in the channel
    2. Post the new dashboard embed
    3. If announcement channel, crosspost the new message
    4. Save the new message ID to state file
    """
    if not channel_id:
        return {"error": "No channel ID provided. Set STRATEGY_STATUS_CHANNEL_ID env var."}

    embed = format_strategy_dashboard()

    if dry_run:
        print("=== DRY RUN ===")
        print(json.dumps(embed, indent=2))
        return {"status": "dry_run", "embed": embed}

    # 1. Delete ALL previous bot messages in the channel
    print(f"  Deleting all previous bot messages in channel...")
    n_deleted = _delete_all_bot_messages(channel_id)
    if n_deleted > 0:
        print(f"  ✅ Deleted {n_deleted} previous message(s)")
    else:
        print(f"  ℹ️ No previous messages to delete")
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

    # 4. Crosspost via webhook (no tombstones) or native (fallback)
    time.sleep(1)
    try:
        sys.path.insert(0, str(pathlib.Path(__file__).parent))
        from webhook_utils import create_crossposter
        wx = create_crossposter(str(channel_id), webhook_name="HermesForge Bot")
        if wx:
            # Delete old webhook messages first
            wx.delete_all()
            time.sleep(0.5)
            # Post new dashboard via webhook
            wx.post(payload)
            print(f"  ✅ Crossposted via webhook to follower server")
        else:
            crosspost_result = _crosspost_message(channel_id, new_msg_id)
            if "id" in crosspost_result:
                print(f"  ✅ Crossposted to followers")
            else:
                print(f"  ℹ️ Not crossposted (not an announcement channel or no followers)")
    except Exception as e:
        print(f"  ℹ️ Webhook crosspost skipped: {e}")
        crosspost_result = _crosspost_message(channel_id, new_msg_id)
        if "id" in crosspost_result:
            print(f"  ✅ Crossposted to followers (native)")

    # 5. Save state
    state = _load_state()
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
