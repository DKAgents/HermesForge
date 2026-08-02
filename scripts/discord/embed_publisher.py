#!/usr/bin/env python3
"""
embed_publisher.py — Posts trade signals as Discord rich embeds.

Each day of the week gets a distinct left-border color:
  Mon=Blue  Tue=Green  Wed=Orange  Thu=Purple  Fri=Red  Sat=Teal  Sun=Gold

Posts directly via Discord Bot API (multipart for chart attachments).
Includes daily header and horizontal rule separators between signals.

Usage (programmatic):
    from embed_publisher import post_daily_batch, post_embed_signal
    post_daily_batch(signals, channel_id, asset_class, regime_data)
"""

import os
import json
import subprocess
import datetime
import pathlib
import time
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from alert_publisher import get_quality_tier, _tradingview_link

# ── Config ────────────────────────────────────────────────────────────────────

DISCORD_BOT_TOKEN = os.environ.get("DISCORD_BOT_TOKEN", "")
API_BASE = "https://discord.com/api/v10"

# Day-of-week colors (Discord embed color is a single integer, 0xRRGGBB)
DAY_COLORS = {
    0: 0x3498db,  # Monday    — Blue
    1: 0x2ecc71,  # Tuesday   — Green
    2: 0xe67e22,  # Wednesday — Orange
    3: 0x9b59b6,  # Thursday  — Purple
    4: 0xe74c3c,  # Friday    — Red
    5: 0x1abc9c,  # Saturday  — Teal
    6: 0xf1c40f,  # Sunday    — Gold
}

DAY_NAMES = [
    "Monday", "Tuesday", "Wednesday", "Thursday",
    "Friday", "Saturday", "Sunday",
]

MONTH_NAMES = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]

# Visual separator for horizontal rules between trades
HR = "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"


# ── Helpers ───────────────────────────────────────────────────────────────────

def get_day_color(dt=None):
    if dt is None:
        dt = datetime.datetime.utcnow()
    return DAY_COLORS.get(dt.weekday(), 0x58a6ff)


def get_day_name(dt=None):
    if dt is None:
        dt = datetime.datetime.utcnow()
    return DAY_NAMES[dt.weekday()]


def _fmt_price(p):
    if abs(p) < 1.0:
        return f"${p:.6f}"
    elif abs(p) < 100.0:
        return f"${p:.4f}"
    else:
        return f"${p:.2f}"


# ── Embed formatting ──────────────────────────────────────────────────────────

def format_signal_embed(signal_dict: dict, color: int) -> dict:
    """Format a signal as a Discord embed JSON object."""
    ticker = signal_dict["ticker"]
    direction = signal_dict.get("direction", "long")
    direction_label = direction.capitalize()
    entry = signal_dict["entry_price"]
    stop = signal_dict["stop_price"]
    target = signal_dict["target_price"]
    strategy_name = signal_dict.get("strategy_name", "Strategy")
    version = signal_dict.get("strategy_version", "1.0")
    publish_channel = signal_dict.get("publish_channel", "stocks")

    tv_url = _tradingview_link(ticker, publish_channel)

    entry_str = _fmt_price(entry)
    stop_pct = abs(entry - stop) / entry * 100 if entry else 0
    stop_str = _fmt_price(stop)
    target_str = _fmt_price(target)
    risk = abs(entry - stop)
    reward = abs(target - entry)
    rr = reward / risk if risk else 0.0

    # Regime
    regime = signal_dict.get("regime", "unknown")
    regime_label = regime.capitalize() if regime != "unknown" else "Unknown"
    benchmark = signal_dict.get("regime_benchmark", "")
    adx = signal_dict.get("regime_adx", "")
    regime_str = regime_label
    extras = []
    if benchmark:
        extras.append(benchmark)
    if adx:
        extras.append(f"ADX {adx}")
    if extras:
        regime_str += f" ({', '.join(extras)})"

    # Quality tier + key conditions
    tier_tag, met_ratio, conditions = get_quality_tier(signal_dict)
    conditions_text = "\n".join(f"• {c}" for c in conditions)

    # Status
    is_live = signal_dict.get("is_live", False)
    status_str = "LIVE" if is_live else "WATCH"

    # Build embed fields
    fields = [
        {"name": "📍 Entry", "value": entry_str, "inline": True},
        {"name": "🛑 Stop", "value": f"{stop_str} ({stop_pct:.1f}% risk)", "inline": True},
        {"name": "🎯 Target", "value": f"{target_str} (R:R {rr:.1f}:1)", "inline": True},
        {"name": "Regime", "value": regime_str, "inline": True},
        {"name": "Confidence", "value": f"{tier_tag} ({met_ratio})", "inline": True},
        {"name": "Status", "value": status_str, "inline": True},
        {"name": "Key Conditions", "value": conditions_text, "inline": False},
    ]

    embed = {
        "title": f"📊 {strategy_name} v{version}",
        "description": f"**{ticker}** | {direction_label} | Daily | [TradingView Chart]({tv_url})",
        "color": color,
        "fields": fields,
        "footer": {"text": "HermesForge Signal Pipeline"},
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
    }

    return embed


def format_daily_header(asset_class: str, regime_data: dict, signal_count: int,
                        live_count: int, watch_count: int, strategies: list,
                        color: int) -> dict:
    """Format the daily header as a Discord embed."""
    dt = datetime.datetime.utcnow()
    day_name = get_day_name(dt)
    date_str = f"{day_name.upper()}, {MONTH_NAMES[dt.month - 1].upper()} {dt.day}, {dt.year}"

    regime = regime_data.get("regime", "unknown")
    regime_label = regime.capitalize() if regime != "unknown" else "Unknown"
    benchmark = regime_data.get("benchmark", "")
    adx = regime_data.get("adx", "")
    regime_str = regime_label
    if benchmark:
        regime_str += f" ({benchmark}"
        if adx:
            regime_str += f", ADX {adx}"
        regime_str += ")"

    asset_emoji = "📈" if asset_class == "stock" else "₿"
    asset_label = "Stock Setups" if asset_class == "stock" else "Crypto Setups"

    description = (
        f"{asset_emoji} **{asset_label}**\n"
        f"Regime: **{regime_str}**\n"
        f"Signals: **{signal_count}** ({live_count} live, {watch_count} watch)\n"
        f"Strategies: {', '.join(strategies) if strategies else 'none active'}"
    )

    embed = {
        "title": f"📅 {date_str}",
        "description": description,
        "color": color,
        "footer": {"text": f"HermesForge Daily Pipeline — {dt.strftime('%H:%M')} UTC"},
    }

    return embed


# ── Discord API posting ───────────────────────────────────────────────────────

def _post_to_discord(channel_id: str, payload: dict, chart_path: str | None = None) -> dict:
    """Post a message to Discord via Bot API. Returns {status, message_id}."""
    url = f"{API_BASE}/channels/{channel_id}/messages"

    if chart_path and os.path.exists(chart_path):
        # Multipart: upload chart + embed
        cmd = [
            "curl", "-s", "-X", "POST",
            "-H", f"Authorization: Bot {DISCORD_BOT_TOKEN}",
            "-F", f"payload_json={json.dumps(payload)}",
            "-F", f"files[0]=@{chart_path};type=image/png",
            url,
        ]
    else:
        # JSON only (no file)
        cmd = [
            "curl", "-s", "-X", "POST",
            "-H", f"Authorization: Bot {DISCORD_BOT_TOKEN}",
            "-H", "Content-Type: application/json",
            "-d", json.dumps(payload),
            url,
        ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

    try:
        response = json.loads(result.stdout)
        if "id" in response:
            return {"status": "ok", "message_id": response["id"]}
        else:
            return {"status": "error", "response": result.stdout[:500]}
    except (json.JSONDecodeError, KeyError):
        return {"status": "error", "response": result.stdout[:500]}


def post_embed_signal(signal_dict: dict, chart_path: str, channel_id: str,
                      color: int, dry_run: bool = False) -> dict:
    """Post a single signal as a Discord embed with chart attachment."""
    embed = format_signal_embed(signal_dict, color)

    # Add image reference if chart exists
    has_chart = chart_path and os.path.exists(chart_path)
    if has_chart:
        embed["image"] = {"url": "attachment://chart.png"}

    payload = {"embeds": [embed]}

    if dry_run:
        return {
            "status": "dry_run",
            "embed": embed,
            "chart_path": chart_path if has_chart else None,
        }

    return _post_to_discord(channel_id, payload, chart_path if has_chart else None)


def post_daily_header(asset_class: str, regime_data: dict, signal_count: int,
                      live_count: int, watch_count: int, strategies: list,
                      channel_id: str, color: int, dry_run: bool = False) -> dict:
    """Post the daily header embed."""
    embed = format_daily_header(asset_class, regime_data, signal_count,
                                live_count, watch_count, strategies, color)
    payload = {"embeds": [embed]}

    if dry_run:
        return {"status": "dry_run", "embed": embed}

    return _post_to_discord(channel_id, payload)


def post_separator(channel_id: str, color: int, dry_run: bool = False) -> dict:
    """Post a horizontal rule separator between signals."""
    embed = {
        "description": HR,
        "color": color,
    }
    payload = {"embeds": [embed]}

    if dry_run:
        return {"status": "dry_run"}

    return _post_to_discord(channel_id, payload)


# ── Batch posting ─────────────────────────────────────────────────────────────

def post_daily_batch(signals: list, channel_id: str, asset_class: str,
                     regime_data: dict, dry_run: bool = False) -> dict:
    """
    Post a full daily batch: header → signals (with separators) → done.

    Args:
        signals: list of signal dicts (sorted by score, enriched with metadata)
        channel_id: Discord channel ID string
        asset_class: "stock" or "crypto"
        regime_data: regime dict from regime_detector
        dry_run: if True, format only (no posting)

    Returns:
        {posted, errors, message_ids, header_id}
    """
    color = get_day_color()
    live_count = sum(1 for s in signals if s.get("is_live", False))
    watch_count = len(signals) - live_count

    # Collect unique strategy names
    strategy_names = sorted(set(s.get("strategy_name", "?") for s in signals))

    result = {
        "posted": 0,
        "errors": 0,
        "message_ids": [],
        "header_id": None,
    }

    # Post daily header
    header_result = post_daily_header(
        asset_class, regime_data, len(signals), live_count, watch_count,
        strategy_names, channel_id, color, dry_run,
    )
    if header_result["status"] in ("ok", "dry_run"):
        result["header_id"] = header_result.get("message_id")
        if not dry_run:
            print(f"  ✅ Daily header posted (ID: {result['header_id']})")
            time.sleep(1)
    else:
        result["errors"] += 1
        print(f"  ❌ Header failed: {header_result.get('response', '')}")
        return result

    # Post each signal with separators
    for i, sig in enumerate(signals):
        # Horizontal rule before each signal (except the first)
        if i > 0 and not dry_run:
            post_separator(channel_id, color, dry_run=False)
            time.sleep(0.5)

        chart_path = sig.get("_chart_path")
        sig_result = post_embed_signal(sig, chart_path, channel_id, color, dry_run)

        if sig_result["status"] in ("ok", "dry_run"):
            result["posted"] += 1
            if not dry_run:
                result["message_ids"].append(sig_result.get("message_id"))
                print(f"  ✅ {sig['ticker']} ({sig.get('direction', '?')}) posted")
                time.sleep(1)
        else:
            result["errors"] += 1
            print(f"  ❌ {sig['ticker']} failed: {sig_result.get('response', '')}")

    return result


# ── Smoke test ────────────────────────────────────────────────────────────────

def _smoke_test():
    """Test embed formatting without posting."""
    signal = {
        "ticker": "BTC",
        "direction": "long",
        "entry_price": 66294.00,
        "stop_price": 62832.24,
        "target_price": 73217.53,
        "strategy_name": "Cross-Sectional Factor",
        "strategy_id": "STR-P-crosssectional",
        "strategy_version": "1.0",
        "publish_channel": "crypto",
        "regime": "ranging",
        "regime_benchmark": "BTC",
        "regime_adx": "10.8",
        "is_live": False,
        "composite_score": 1.88,
        "factor_mom12_1": -0.3,
        "factor_liquid": 2516000000,
        "factor_pricemom": -0.15,
    }

    color = get_day_color()
    embed = format_signal_embed(signal, color)

    print("=== Signal Embed ===")
    print(json.dumps(embed, indent=2))

    regime_data = {"regime": "ranging", "benchmark": "BTC", "adx": "10.8"}
    header = format_daily_header("crypto", regime_data, 16, 0, 16,
                                 ["Cross-Sectional Factor"], color)
    print("\n=== Daily Header ===")
    print(json.dumps(header, indent=2))

    print(f"\n✅ Smoke test passed — day color: 0x{color:06x} ({get_day_name()})")


if __name__ == "__main__":
    if "--smoke-test" in sys.argv:
        _smoke_test()
    else:
        print(__doc__)
