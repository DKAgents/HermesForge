#!/usr/bin/env python3
"""
post_weekly_funnel.py — US-190: post the consolidated per-gate funnel to the
Strategy Status channel once a week (wired via a weekly no-agent cron).

Generates the funnel (consolidated_funnel.build_funnel + markdown formatter) and
posts it to the source-server #strategy-status channel using the same bot-API
mechanism the strategy dashboard uses (DISCORD_BOT_TOKEN). Stdlib-only + a repo
import (consolidated_funnel is itself stdlib-only), so it runs under the single
trading interpreter resolved by resolve_python.sh.

Usage:
    python3 post_weekly_funnel.py           # generate + post
    python3 post_weekly_funnel.py --dry-run # generate only, no post
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys
import urllib.request

REPO = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "scripts" / "gauntlet"))

from consolidated_funnel import build_funnel, _fmt_markdown  # noqa: E402

STRATEGY_STATUS_CHANNEL_ID = os.environ.get("STRATEGY_STATUS_CHANNEL_ID",
                                            "1533332485641998386")


def _post(content: str, channel_id: str) -> bool:
    token = os.environ.get("DISCORD_BOT_TOKEN", "")
    if not token:
        print("missing DISCORD_BOT_TOKEN — cannot post", file=sys.stderr)
        return False
    payload = json.dumps({"content": content}).encode()
    req = urllib.request.Request(
        f"https://discord.com/api/v10/channels/{channel_id}/messages",
        data=payload,
        headers={"Authorization": f"Bot {token}",
                 "Content-Type": "application/json",
                 "User-Agent": "HermesForge/1.0 (post_weekly_funnel)"},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status == 200
    except Exception as e:
        print(f"post failed: {e}", file=sys.stderr)
        return False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    funnel = build_funnel()
    markdown = _fmt_markdown(funnel)

    if args.dry_run:
        print(markdown)
        return 0

    print(markdown)  # also emitted to cron stdout (audit trail)
    ok = _post(markdown, STRATEGY_STATUS_CHANNEL_ID)
    print(f"funnel post: {'ok' if ok else 'failed'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())