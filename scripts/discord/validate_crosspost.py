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

# Per-channel template requirements
RULES = {
    "1528555538848153640": ["Trade ID:", "[GAUNTLET]"],   # stock-setups
    "1528555885310513213": ["Trade ID:", "[GAUNTLET]"],   # crypto-setups
    "1532020053548208328": [],   # daily-market-briefing — any format ok
    "1533332485641998386": [],   # strategy-status
    "1534834809451450409": [],   # strategy-research
    "1537225420120793088": [],   # paper-trading
    "1540951134200402071": ["Trade ID:", "[GAUNTLET]"],   # day-trade-crypto
    "1540951208028803142": ["Trade ID:", "[GAUNTLET]"],   # day-trade-stocks
}


def validate(msg: dict, channel_id: str) -> bool:
    markers = RULES.get(channel_id, [])
    if not markers:
        return True  # No validation for this channel

    # Gather all text: content + embed titles/descriptions/footers
    text = msg.get("content", "") or ""
    for embed in msg.get("embeds", []):
        text += " " + (embed.get("title", "") or "")
        text += " " + (embed.get("description", "") or "")
        footer = embed.get("footer")
        if isinstance(footer, dict):
            text += " " + (footer.get("text", "") or "")

    for marker in markers:
        if marker not in text:
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
        print("skip", flush=True)