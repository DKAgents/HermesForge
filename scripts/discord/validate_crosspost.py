#!/usr/bin/env python3
"""
US-148: Crosspost template validator.

Called by crosspost_webhook_all.sh before forwarding messages.
Reads a Discord message JSON from stdin. Prints "ok" if valid,
"skip" if it should be skipped.

Usage: echo '{"content":"...","embeds":[...]}' | python3 validate_crosspost.py CHANNEL_ID
"""

import sys
import json
import re

# Per-channel template requirements.
# A marker value of "*trade-attribution*" means the message must carry a trade
# identifier: either a "🔖 Trade ID:" label (setup) OR a short-id back-link like
# [BTC-P-0727A](https://discord.com/channels/...) (exit/lifecycle alert).
# "[GAUNTLET]" is intentionally REMOVED — the principal's 2026-10-31 decision
# strips the "[GAUNTLET]" prefix and version strings from the setup template.
TRADE_ATTRIBUTION = "*trade-attribution*"

RULES = {
    "1528555538848153640": [TRADE_ATTRIBUTION],           # stock-setups
    "1528555885310513213": [TRADE_ATTRIBUTION],           # crypto-setups
    "1532020053548208328": ["# Daily Market Briefing"],   # daily-market-briefing
    "1533332485641998386": [None],   # strategy-status — any real content OK, but must pass blacklist
    "1534834809451450409": [None],   # strategy-research
    "1537225420120793088": [None],   # paper-trading
    "1540951134200402071": [TRADE_ATTRIBUTION],           # day-trade-crypto
    "1540951208028803142": [TRADE_ATTRIBUTION],           # day-trade-stocks
}

# A short-id back-link: [TICKER-STRAT-MMDDS](https://discord.com/channels/...)
SHORT_ID_LINK_RE = re.compile(r"\[[A-Z0-9]{1,12}-[A-Z]-\d{4}[A-Z]\]\(")


def _has_trade_attribution(text: str) -> bool:
    """Setup has "Trade ID:"; exit/lifecycle alert has a short-id back-link."""
    return ("Trade ID:" in text) or bool(SHORT_ID_LINK_RE.search(text))

# Global blacklist: messages matching any of these patterns are NEVER forwarded
GLOBAL_BLACKLIST = [
    "Cronjob Response:",     # Cron wrapper headers
    "**Job ID:**",           # Cron metadata
    "**Run Time:**",         # Cron metadata
    "Cron Job:",             # Cron headers (alternate format)
    "Watchdog Alert",        # Watchdog alerts
    "stopped retrying",      # Tool guardrail errors
    "same_tool_failure",     # Tool guardrail errors
]


def validate(msg: dict, channel_id: str) -> bool:
    """Check if message should be crossposted. Returns False to skip."""
    # ── Global blacklist: never forward cron metadata or error messages ──
    text = msg.get("content", "") or ""
    for embed in msg.get("embeds", []):
        text += " " + (embed.get("title", "") or "")
        text += " " + (embed.get("description", "") or "")
        footer = embed.get("footer")
        if isinstance(footer, dict):
            text += " " + (footer.get("text", "") or "")

    for pattern in GLOBAL_BLACKLIST:
        if pattern.lower() in text.lower():
            return False

    # ── Per-channel markers ──
    markers = RULES.get(channel_id, [])
    if not markers:
        return True  # No rules for this channel, just blacklist

    # None marker = any real content OK (blacklist handles filtering)
    if markers == [None]:
        return bool(text.strip())

    # Specific markers must all be present
    for marker in markers:
        if marker == TRADE_ATTRIBUTION:
            ok = _has_trade_attribution(text)
        else:
            ok = marker in text
        if not ok:
            return False
    return True


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("skip", flush=True)
        sys.exit(0)

    channel_id = sys.argv[1]
    raw = sys.stdin.read().strip()

    if not raw:
        print("skip", flush=True)
        sys.exit(0)

    try:
        msg = json.loads(raw)
    except json.JSONDecodeError:
        print("skip", flush=True)
        sys.exit(0)

    if validate(msg, channel_id):
        print("ok", flush=True)
    else:
        msg_id = msg.get("id", "?")
        content_preview = (msg.get("content", "") or "")[:60]
        print(f"⛔ Crosspost BLOCKED — msg {msg_id} in channel {channel_id}: {content_preview}", file=sys.stderr)
        print("skip", flush=True)