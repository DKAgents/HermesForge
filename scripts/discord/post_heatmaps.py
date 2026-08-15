#!/usr/bin/env python3
"""
post_heatmaps.py
================
HermesForge — Generate and post heatmaps to Discord channels.

Wiring:
  1. Daily Briefing (#daily-market-briefing, 1532020053548208328):
     - Correlation heatmap
     - Sector rotation heatmap
  2. Weekly Research (#strategy-research, 1534834809451450409):
     - All 4 heatmaps (correlation, strategy-regime, crypto performance, sector rotation)
  3. Performance Report (#paper-trading, 1537225420120793088):
     - Strategy-regime heatmap

Usage:
    python3 post_heatmaps.py --daily        # post correlation + sector to daily briefing
    python3 post_heatmaps.py --weekly       # post all 4 to strategy-research
    python3 post_heatmaps.py --performance  # post strategy-regime to paper-trading
    python3 post_heatmaps.py --all          # post all to all channels
"""

import sys
import os
import argparse
import pathlib
import requests

REPO_ROOT = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "data"))

HEATMAP_DIR = pathlib.Path.home() / ".hermes" / "market_data" / "heatmaps"

# Discord channel IDs
CHANNEL_DAILY_BRIEFING = "1532020053548208328"
CHANNEL_STRATEGY_RESEARCH = "1534834809451450409"
CHANNEL_PAPER_TRADING = "1537225420120793088"

# Heatmap files
HEATMAPS = {
    "correlation": HEATMAP_DIR / "correlation_heatmap.png",
    "strategy_regime": HEATMAP_DIR / "strategy_regime_heatmap.png",
    "crypto_performance": HEATMAP_DIR / "crypto_performance_heatmap.png",
    "sector_rotation": HEATMAP_DIR / "sector_rotation_heatmap.png",
}

# Channel webhook URLs (loaded from env)
def _get_webhooks():
    """Get webhook URLs from environment."""
    webhooks = {}
    for key in os.environ:
        if key.startswith("WEBHOOK_") and key.endswith("_URL"):
            channel = key.replace("WEBHOOK_", "").replace("_URL", "").lower()
            webhooks[channel] = os.environ[key]
    return webhooks


def _post_via_discord_bot(channel_id: str, message: str, file_path: str = None):
    """Post message + optional file to Discord via bot API."""
    token = os.environ.get("DISCORD_BOT_TOKEN", "")
    if not token:
        print(f"  [ERROR] DISCORD_BOT_TOKEN not set")
        return False
    
    url = f"https://discord.com/api/v10/channels/{channel_id}/messages"
    headers = {"Authorization": f"Bot {token}"}
    
    try:
        if file_path and os.path.exists(file_path):
            # Post with file attachment
            with open(file_path, "rb") as f:
                files = {"files[0]": (os.path.basename(file_path), f, "image/png")}
                payload = {"content": message}
                r = requests.post(url, headers=headers, data=payload, files=files, timeout=15)
        else:
            payload = {"content": message}
            r = requests.post(url, headers=payload, json=payload, timeout=15)
        
        if r.status_code in (200, 201):
            print(f"  Posted to {channel_id}: {message[:60]}...")
            return True
        else:
            print(f"  [ERROR] Discord API returned {r.status_code}: {r.text[:200]}")
            return False
    except Exception as e:
        print(f"  [ERROR] Failed to post: {e}")
        return False


def generate_heatmaps():
    """Generate all 4 heatmaps."""
    from visualize_heatmaps import (
        generate_correlation_heatmap,
        generate_strategy_regime_heatmap,
        generate_crypto_performance_heatmap,
        generate_sector_rotation_heatmap,
    )
    
    print("Generating heatmaps...")
    for name, fn in [
        ("correlation", generate_correlation_heatmap),
        ("strategy_regime", generate_strategy_regime_heatmap),
        ("crypto_performance", generate_crypto_performance_heatmap),
        ("sector_rotation", generate_sector_rotation_heatmap),
    ]:
        try:
            path = fn()
            if path:
                print(f"  {name}: {path.name} ({path.stat().st_size // 1024}KB)")
            else:
                print(f"  {name}: FAILED")
        except Exception as e:
            print(f"  {name}: ERROR - {e}")


def post_daily_briefing():
    """Post correlation + sector rotation heatmaps to daily briefing."""
    print("\n── Daily Briefing Heatmaps ──")
    
    # Post correlation heatmap
    if HEATMAPS["correlation"].exists():
        _post_via_discord_bot(
            CHANNEL_DAILY_BRIEFING,
            "📊 **Cross-Asset Correlation Heatmap** — Current regime snapshot",
            str(HEATMAPS["correlation"]),
        )
    
    # Post sector rotation heatmap
    if HEATMAPS["sector_rotation"].exists():
        _post_via_discord_bot(
            CHANNEL_DAILY_BRIEFING,
            "📊 **Sector Rotation Heatmap** — Leading/lagging sectors vs SPY",
            str(HEATMAPS["sector_rotation"]),
        )


def post_weekly_research():
    """Post all 4 heatmaps to strategy-research."""
    print("\n── Weekly Research Heatmaps ──")
    
    descriptions = {
        "correlation": "📊 **Cross-Asset Correlation Heatmap** — 30-day rolling correlations",
        "strategy_regime": "📊 **Strategy-Regime Performance Heatmap** — Win rate by strategy × regime",
        "crypto_performance": "📊 **Crypto Performance Heatmap** — Top crypto assets performance",
        "sector_rotation": "📊 **Sector Rotation Heatmap** — ETF performance vs SPY",
    }
    
    for name, path in HEATMAPS.items():
        if path.exists():
            _post_via_discord_bot(
                CHANNEL_STRATEGY_RESEARCH,
                descriptions[name],
                str(path),
            )


def post_performance_report():
    """Post strategy-regime heatmap to paper-trading."""
    print("\n── Performance Report Heatmap ──")
    
    if HEATMAPS["strategy_regime"].exists():
        _post_via_discord_bot(
            CHANNEL_PAPER_TRADING,
            "📊 **Strategy-Regime Performance Heatmap** — Which strategies work in which regimes",
            str(HEATMAPS["strategy_regime"]),
        )


def main():
    ap = argparse.ArgumentParser(description="Post heatmaps to Discord channels")
    ap.add_argument("--daily", action="store_true", help="Post to daily briefing")
    ap.add_argument("--weekly", action="store_true", help="Post to strategy research")
    ap.add_argument("--performance", action="store_true", help="Post to paper trading")
    ap.add_argument("--all", action="store_true", help="Post all to all channels")
    ap.add_argument("--generate", action="store_true", help="Regenerate heatmaps before posting")
    args = ap.parse_args()
    
    if args.generate:
        generate_heatmaps()
    
    if args.all:
        post_daily_briefing()
        post_weekly_research()
        post_performance_report()
    elif args.daily:
        post_daily_briefing()
    elif args.weekly:
        post_weekly_research()
    elif args.performance:
        post_performance_report()
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
