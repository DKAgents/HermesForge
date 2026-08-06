#!/usr/bin/env python3
"""
research_publisher.py — HermesForge Research Results Publisher

Posts the weekly research pipeline results to the #strategy-research
Discord channel as a rich embed with a colored left border that rotates
by day of week. Deletes all previous bot messages first, then crossposts.

Day-of-week color mapping (matches the trading-setup convention):
  Mon=#3498db (blue), Tue=#2ecc71 (green), Wed=#e67e22 (orange),
  Thu=#9b59b6 (purple), Fri=#e74c3c (red), Sat=#1abc9c (teal),
  Sun=#f1c40f (gold)

Usage:
    python3 research_publisher.py                    # post + crosspost
    python3 research_publisher.py --dry-run           # format only
    python3 research_publisher.py --channel-id <id>   # override channel
"""

import os
import sys
import json
import subprocess
import pathlib
import datetime
import time
import glob

REPO_ROOT = pathlib.Path(__file__).parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "discord"))

DISCORD_BOT_TOKEN = os.environ.get("DISCORD_BOT_TOKEN", "")
API_BASE = "https://discord.com/api/v10"

CHANNEL_ID = os.environ.get("STRATEGY_RESEARCH_CHANNEL_ID", "1534834809451450409")

RESEARCH_DATA_DIR = REPO_ROOT / "data"

# ── Day-of-Week Color Mapping ────────────────────────────────────────────────

DAY_COLORS = {
    0: 0x3498db,  # Monday    — blue
    1: 0x2ecc71,  # Tuesday   — green
    2: 0xe67e22,  # Wednesday — orange
    3: 0x9b59b6,  # Thursday  — purple
    4: 0xe74c3c,  # Friday    — red
    5: 0x1abc9c,  # Saturday  — teal
    6: 0xf1c40f,  # Sunday    — gold
}

DAY_NAMES = {
    0: "Monday", 1: "Tuesday", 2: "Wednesday", 3: "Thursday",
    4: "Friday", 5: "Saturday", 6: "Sunday",
}


# ── Load Latest Research ──────────────────────────────────────────────────────

def _load_latest_research() -> dict:
    """Load the most recent research pipeline JSON output."""
    pattern = str(RESEARCH_DATA_DIR / "research-*.json")
    files = sorted(glob.glob(pattern))
    if not files:
        return {}
    with open(files[-1]) as f:
        return json.load(f)


# ── Format Embed ──────────────────────────────────────────────────────────────

def _format_factor_summary(fs_data: dict, asset_label: str) -> list:
    """Format factor screener findings for one asset class. Returns lines."""
    lines = []
    n_cands = fs_data.get("n_candidates", 0)
    n_tested = fs_data.get("n_factors_tested", 0)
    lines.append(f"**{n_tested} factors tested | {n_cands} candidate(s) flagged**")

    candidates = fs_data.get("candidates", [])
    if candidates:
        for c in candidates:
            factor = c.get("factor", "?")
            sharpe = c.get("sharpe", 0)
            p_val = c.get("p_value", 1)
            ann_ret = c.get("annualized_return", 0)
            direction = "inverted" if sharpe < 0 else "normal"
            lines.append(
                f"  ★ **{factor}**: Sharpe {sharpe:.2f}, p={p_val:.4f}, "
                f"annual {ann_ret*100:.1f}% ({direction})"
            )
    else:
        lines.append("  *No candidates this run.*")
    return lines


def _format_revival(rt_data: dict) -> list:
    """Format revival tester findings. Returns lines."""
    lines = []
    n_tested = rt_data.get("strategies_tested", 0)
    n_cands = rt_data.get("n_candidates", 0)
    lines.append(f"**{n_tested} killed strategies re-tested | {n_cands} revival candidate(s)**")

    candidates = rt_data.get("candidates", [])
    if candidates:
        for c in candidates:
            strat = c.get("strategy", "?")
            name = c.get("name", "?")
            mean_r = c.get("mean_r", 0)
            p_val = c.get("p_value", 1)
            n_sig = c.get("n_signals", 0)
            hit_rate = c.get("hit_rate", 0)
            lines.append(
                f"  ★ **{strat} ({name})**: Mean R={mean_r:.4f}, p={p_val:.4f}, "
                f"{n_sig} signals, {hit_rate*100:.0f}% hit rate"
            )
    else:
        lines.append("  *No revival candidates — all killed strategies remain dead.*")
    return lines


def _format_decay(dm_data: dict) -> list:
    """Format decay monitor findings. Returns lines."""
    lines = []
    n_monitored = dm_data.get("strategies_monitored", 0)
    n_decayed = dm_data.get("n_decayed", 0)
    lines.append(f"**{n_monitored} strategies monitored | {n_decayed} decay flag(s)**")

    decayed = dm_data.get("decayed", [])
    if decayed:
        for d in decayed:
            strat = d.get("strategy", "?")
            name = d.get("name", "?")
            decay_pct = d.get("decay_pct", 0)
            first_sharpe = d.get("first_sharpe", 0)
            curr_sharpe = d.get("sharpe_proxy", 0)
            lines.append(
                f"  ⚠️ **{strat} ({name})**: Sharpe dropped from "
                f"{first_sharpe:.2f} to {curr_sharpe:.2f} ({decay_pct*100:.0f}%)"
            )
    else:
        lines.append("  ✓ All monitored strategies stable — no edge decay detected.")

    # Show current stats for monitored strategies
    results = dm_data.get("results", [])
    if results:
        lines.append("")
        lines.append("  *Current strategy health:*")
        for r in results:
            if "error" in r:
                continue
            strat = r.get("strategy", "?")
            mean_r = r.get("mean_r", 0)
            sharpe = r.get("sharpe_proxy", 0)
            p_val = r.get("p_value", 1)
            n_sig = r.get("n_signals", 0)
            lines.append(
                f"  {strat}: R={mean_r:.3f}, Sharpe={sharpe:.2f}, "
                f"p={p_val:.3f}, {n_sig} signals"
            )
    return lines


def _format_hypotheses(hg_data: dict, asset_label: str) -> list:
    """Format hypothesis generator findings. Returns lines."""
    lines = []
    n_tested = hg_data.get("n_hypotheses_tested", 0)
    n_cands = hg_data.get("n_candidates", 0)
    top_factors = hg_data.get("top_factors", [])
    lines.append(f"**{n_tested} hypotheses tested | {n_cands} candidate(s)**")
    if top_factors:
        lines.append(f"  Top factors: {', '.join(top_factors)}")

    candidates = hg_data.get("candidates", [])
    if candidates:
        for c in candidates:
            hyp = c.get("hypothesis", "?")
            sharpe = c.get("sharpe", 0)
            p_val = c.get("p_value", 1)
            lines.append(f"  ★ **{hyp}**: Sharpe {sharpe:.2f}, p={p_val:.4f}")
    else:
        lines.append("  *No new strategy candidates this run.*")
    return lines


def format_research_embed() -> dict:
    """Format the research pipeline results as a Discord embed."""
    dt = datetime.datetime.utcnow()
    dow = dt.weekday()
    color = DAY_COLORS[dow]
    day_name = DAY_NAMES[dow]

    research = _load_latest_research()
    if not research:
        return {
            "title": "📊 HermesForge Weekly Research Report",
            "description": "No research data found. Pipeline may not have run yet.",
            "color": color,
            "timestamp": dt.isoformat() + "Z",
        }

    ts = research.get("timestamp", "unknown")[:16].replace("T", " ")
    runtime = research.get("runtime_seconds", 0)
    total_items = research.get("total_action_items", 0)

    # ── Build description ──
    desc_lines = [
        f"**{day_name}, {dt.strftime('%Y-%m-%d %H:%M')} UTC**",
        f"Pipeline runtime: {runtime:.0f}s | Action items: {total_items}",
    ]

    # Executive summary
    fs = research.get("factor_screener", {})
    rt = research.get("revival_tester", {})
    dm = research.get("decay_monitor", {})
    hg = research.get("hypothesis_generator", {})

    stock_fs = fs.get("stock", {})
    crypto_fs = fs.get("crypto", {})
    stock_hg = hg.get("stock", {})
    crypto_hg = hg.get("crypto", {})

    desc_lines.append("")
    desc_lines.append(f"🔬 Factor anomalies: {stock_fs.get('n_candidates',0)} stocks, {crypto_fs.get('n_candidates',0)} crypto")
    desc_lines.append(f"♻️ Revival candidates: {rt.get('n_candidates',0)}")
    desc_lines.append(f"📉 Edge decay: {dm.get('n_decayed',0)}")
    desc_lines.append(f"💡 New strategy candidates: {stock_hg.get('n_candidates',0)} stocks, {crypto_hg.get('n_candidates',0)} crypto")

    # ── Build fields ──
    fields = []

    # Factor screener
    field_lines = []
    field_lines.append("**Stocks:**")
    field_lines.extend(_format_factor_summary(stock_fs, "Stocks"))
    field_lines.append("")
    field_lines.append("**Crypto:**")
    field_lines.extend(_format_factor_summary(crypto_fs, "Crypto"))
    fields.append({
        "name": "🔬 Factor Screener",
        "value": "\n".join(field_lines)[:1024],
        "inline": False,
    })

    # Revival tester
    fields.append({
        "name": "♻️ Killed Strategy Revival",
        "value": "\n".join(_format_revival(rt))[:1024],
        "inline": False,
    })

    # Decay monitor
    decay_lines = _format_decay(dm)
    fields.append({
        "name": "📉 Edge Decay Monitor",
        "value": "\n".join(decay_lines)[:1024],
        "inline": False,
    })

    # Hypothesis generator
    hyp_lines = []
    hyp_lines.append("**Stocks:**")
    hyp_lines.extend(_format_hypotheses(stock_hg, "Stocks"))
    hyp_lines.append("")
    hyp_lines.append("**Crypto:**")
    hyp_lines.extend(_format_hypotheses(crypto_hg, "Crypto"))
    fields.append({
        "name": "💡 Hypothesis Generator",
        "value": "\n".join(hyp_lines)[:1024],
        "inline": False,
    })

    # Action items summary
    action_lines = []
    if total_items == 0:
        action_lines.append("*No new edges found this week. All strategies stable.*")
    else:
        action_lines.append(f"**{total_items} item(s) require investigation:**")
        if stock_fs.get("n_candidates",0) + crypto_fs.get("n_candidates",0) > 0:
            action_lines.append(f"  • Factor anomalies: design strategies around inverted factors")
        if rt.get("n_candidates",0) > 0:
            action_lines.append(f"  • Revival candidates: re-run full walk-forward validation")
        if dm.get("n_decayed",0) > 0:
            action_lines.append(f"  • Decay flags: investigate and consider strategy retirement")
        if stock_hg.get("n_candidates",0) + crypto_hg.get("n_candidates",0) > 0:
            action_lines.append(f"  • New hypotheses: full walk-forward validation needed")
    action_lines.append("")
    action_lines.append(f"Full report: `vault/research/research-{dt.strftime('%Y-%m-%d')}.md`")

    fields.append({
        "name": "🎯 Action Items",
        "value": "\n".join(action_lines)[:1024],
        "inline": False,
    })

    embed = {
        "title": "📊 HermesForge Weekly Research Report",
        "description": "\n".join(desc_lines),
        "color": color,
        "fields": fields,
        "footer": {
            "text": f"Research Pipeline | {day_name} border color: #{color:06x}"
        },
        "timestamp": dt.isoformat() + "Z",
    }

    return embed


# ── Discord API helpers ──────────────────────────────────────────────────────

def _api_request(method: str, url: str, data: dict = None) -> dict:
    """Make a Discord API request."""
    cmd = ["curl", "-s", "-X", method, "-H", f"Authorization: Bot {DISCORD_BOT_TOKEN}"]
    if data:
        cmd += ["-H", "Content-Type: application/json", "-d", json.dumps(data)]
    cmd += [url]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    try:
        return json.loads(result.stdout)
    except (json.JSONDecodeError, ValueError):
        return {"error": result.stdout[:500]}


def _get_all_messages(channel_id: str) -> list:
    """Fetch all messages from the channel (up to 100)."""
    url = f"{API_BASE}/channels/{channel_id}/messages?limit=100"
    result = _api_request("GET", url)
    if isinstance(result, list):
        return result
    return []


def _delete_message(channel_id: str, message_id: str) -> dict:
    """Delete a message from a channel."""
    return _api_request("DELETE", f"{API_BASE}/channels/{channel_id}/messages/{message_id}")


def _crosspost_message(channel_id: str, message_id: str) -> dict:
    """Crosspost (publish) a message from an announcement channel."""
    return _api_request("POST", f"{API_BASE}/channels/{channel_id}/messages/{message_id}/crosspost")


def _delete_all_bot_messages(channel_id: str) -> int:
    """Delete all messages posted by the bot in the channel. Returns count deleted."""
    messages = _get_all_messages(channel_id)
    deleted = 0
    for msg in messages:
        author = msg.get("author", {})
        if author.get("bot") and author.get("username", "").startswith("Trading Swarm"):
            msg_id = msg.get("id")
            if msg_id:
                _delete_message(channel_id, msg_id)
                deleted += 1
                time.sleep(0.6)
    return deleted


# ── Main ──────────────────────────────────────────────────────────────────────

def post_research_report(channel_id: str = CHANNEL_ID, dry_run: bool = False) -> dict:
    """Post the research report embed, replacing all previous posts, then crosspost."""
    embed = format_research_embed()

    if dry_run:
        print("=== DRY RUN ===")
        print(json.dumps(embed, indent=2))
        return {"status": "dry_run", "embed": embed}

    if not DISCORD_BOT_TOKEN:
        return {"error": "DISCORD_BOT_TOKEN not set"}

    # 1. Delete all previous bot messages
    print("  Deleting all previous bot messages...")
    n_deleted = _delete_all_bot_messages(channel_id)
    if n_deleted > 0:
        print(f"  ✅ Deleted {n_deleted} previous message(s)")
    else:
        print("  ℹ️ No previous messages to delete")
    time.sleep(1)

    # 2. Post new embed
    payload = {"embeds": [embed]}
    result = _api_request("POST", f"{API_BASE}/channels/{channel_id}/messages", payload)
    if "id" not in result:
        return {"error": "Failed to post", "response": result}

    msg_id = result["id"]
    print(f"  ✅ Report posted (msg {msg_id})")

    # 3. Crosspost
    time.sleep(1)
    crosspost_result = _crosspost_message(channel_id, msg_id)
    if "id" in crosspost_result:
        print(f"  ✅ Crossposted to followers")
    else:
        print(f"  ℹ️ Not crossposted ({crosspost_result.get('message', 'unknown')})")

    return {"status": "ok", "message_id": msg_id}


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="HermesForge Research Publisher")
    ap.add_argument("--dry-run", action="store_true", help="Format only, no posting")
    ap.add_argument("--channel-id", type=str, default=None, help="Override channel ID")
    args = ap.parse_args()

    ch_id = args.channel_id or CHANNEL_ID
    result = post_research_report(ch_id, dry_run=args.dry_run)
    if "error" in result:
        print(f"ERROR: {result['error']}")
        sys.exit(1)
    print("Done.")
