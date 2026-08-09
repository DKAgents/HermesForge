#!/usr/bin/env python3
"""
linkedin_filters.py - HermesForge LinkedIn Post Filters

Programmatic guards for LinkedIn post quality:
  1. strip_em_dashes() - Replace all em-dash/en-dash chars with safe alternatives
  2. check_topic_uniqueness() - Fetch last N posts from channel, detect topic category,
     enforce no-back-to-back-same-category rule

Usage from cron:
  from linkedin_filters import strip_em_dashes, check_topic_uniqueness
  clean_text = strip_em_dashes(raw_text)
  uniqueness = check_topic_uniqueness(channel_id, proposed_text)
  if uniqueness["blocked"]:
      # pick a different topic
"""

import re
import os
import json
import subprocess
import sys
from typing import Optional

# Em-dash and en-dash Unicode chars
EM_DASH = "\u2014"      # —
EN_DASH = "\u2013"      # –
HYPHEN = "\u2010"       # ‐ (non-breaking hyphen, also replace)
FIGURE_DASH = "\u2012"  # ‒
HORIZONTAL_BAR = "\u2015"  # ―

# All dash-like chars that should be replaced
DASH_CHARS = [EM_DASH, EN_DASH, HYPHEN, FIGURE_DASH, HORIZONTAL_BAR]

# Category keywords for topic detection
TOPIC_CATEGORIES = {
    "duplicate_data": ["duplicate", "dedup", "deduplication", "duplicate record", "data quality"],
    "digital_transformation": ["digital transformation", "modernization", "legacy", "transformation"],
    "ai_agent_readiness": ["agentforce", "ai agent", "agent readiness", "copilot", "ai readiness"],
    "data_pipelines": ["data cloud", "data pipeline", "ingestion", "data volume", "consumption"],
    "config_technical_debt": ["technical debt", "configuration", "validation rule", "flow", "apex", "custom field"],
    "news_events": ["announce", "release", "update", "keynote", "dreamforce", "earnings", "downgrade", "upgrade"],
}


def strip_em_dashes(text: str) -> str:
    """
    Replace all em-dash, en-dash, and similar Unicode dash characters
    with safe alternatives (regular hyphens, commas, or parentheses).

    This is a HARD filter - it runs on every LinkedIn post before posting.
    The LLM has repeatedly failed to self-police this rule.
    """
    # Replace em-dash with regular hyphen (most common case)
    # Context-aware replacement for better readability
    for dash in DASH_CHARS:
        text = text.replace(dash, "-")
    
    # Also handle the HTML entity version just in case
    text = text.replace("&mdash;", "-")
    text = text.replace("&ndash;", "-")
    text = text.replace("&#8212;", "-")
    text = text.replace("&#8211;", "-")
    
    return text


def verify_no_dashes(text: str) -> bool:
    """Verify that text contains zero em-dash or en-dash characters."""
    for dash in DASH_CHARS:
        if dash in text:
            return False
    return True


def detect_category(text: str) -> str:
    """
    Detect the topic category of a LinkedIn post based on keyword matching.
    Returns the category name, or 'other' if no match.
    """
    text_lower = text.lower()
    scores = {}
    for category, keywords in TOPIC_CATEGORIES.items():
        score = sum(1 for kw in keywords if kw in text_lower)
        if score > 0:
            scores[category] = score
    
    if scores:
        return max(scores.items(), key=lambda x: x[1])[0]
    return "other"


def fetch_recent_posts(channel_id: str, limit: int = 5) -> list[str]:
    """
    Fetch the last N bot messages from a Discord channel via the REST API.
    Returns a list of message content strings.
    """
    token = os.environ.get("DISCORD_BOT_TOKEN", "")
    if not token:
        print("WARNING: DISCORD_BOT_TOKEN not set, cannot fetch recent posts", file=sys.stderr)
        return []
    
    url = f"https://discord.com/api/v10/channels/{channel_id}/messages?limit={limit}"
    result = subprocess.run(
        ["curl", "-s", "-H", f"Authorization: Bot {token}", url],
        capture_output=True, text=True, timeout=15
    )
    
    try:
        messages = json.loads(result.stdout)
        if isinstance(messages, list):
            return [msg.get("content", "") for msg in messages if msg.get("content")]
    except (json.JSONDecodeError, ValueError):
        pass
    
    return []


def check_topic_uniqueness(channel_id: str, proposed_text: str, limit: int = 5) -> dict:
    """
    Check if the proposed post's topic category matches any of the last N posts.
    
    Returns:
        {
            "blocked": bool,          # True if back-to-back same category
            "category": str,          # Detected category of proposed post
            "recent_categories": list, # Categories of last N posts
            "last_category": str,     # Category of most recent post
        }
    """
    recent_posts = fetch_recent_posts(channel_id, limit)
    recent_categories = [detect_category(p) for p in recent_posts if p.strip()]
    
    proposed_category = detect_category(proposed_text)
    last_category = recent_categories[0] if recent_categories else "none"
    
    blocked = (proposed_category == last_category) and proposed_category != "other"
    
    return {
        "blocked": blocked,
        "category": proposed_category,
        "recent_categories": recent_categories,
        "last_category": last_category,
        "message": f"Proposed category '{proposed_category}' matches last post category '{last_category}'" if blocked else f"OK: proposed '{proposed_category}', last was '{last_category}'",
    }


# CLI for testing
if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="LinkedIn post filters")
    ap.add_argument("--test-dashes", action="store_true", help="Test em-dash stripping")
    ap.add_argument("--test-category", type=str, help="Test category detection on given text")
    ap.add_argument("--check-uniqueness", type=str, help="Check topic uniqueness (pass channel ID, read post from stdin)")
    args = ap.parse_args()
    
    if args.test_dashes:
        test = "This is a test—with an em-dash—and an en–dash too."
        clean = strip_em_dashes(test)
        print(f"Original: {test}")
        print(f"Clean:    {clean}")
        print(f"Verify:   {'PASS' if verify_no_dashes(clean) else 'FAIL'}")
    
    if args.test_category:
        cat = detect_category(args.test_category)
        print(f"Category: {cat}")
    
    if args.check_uniqueness:
        post_text = sys.stdin.read().strip()
        if post_text:
            result = check_topic_uniqueness(args.check_uniqueness, post_text)
            print(json.dumps(result, indent=2))
