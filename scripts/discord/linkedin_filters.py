#!/usr/bin/env python3
"""
linkedin_filters.py - HermesForge LinkedIn Post Filters

Programmatic guards for LinkedIn post quality:
  1. strip_em_dashes() - Replace all em-dash/en-dash chars with safe alternatives
  2. check_topic_uniqueness() - Fetch last N posts, detect topic category,
     enforce a minimum cooldown window between same-category posts.
     When a topic IS within cooldown, suggests cross-referencing the earlier post.

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

# Category keywords for topic detection — expanded to catch semantic matches
TOPIC_CATEGORIES = {
    "duplicate_data": [
        "duplicate", "dedup", "deduplication", "duplicate record",
        "data quality", "matching rule", "match rule", "duplicate rule",
        "duplicate record set", "duplicate management", "duplicate check",
        "acme corp", "acme corporation", "erp migration", "org merge",
        "merge accounts", "duplicate contact", "duplicate account",
        "record merge", "data deduplication", "duplicate detection",
    ],
    "digital_transformation": [
        "digital transformation", "modernization", "legacy", "transformation",
        "legacy migration", "legacy system",
    ],
    "ai_agent_readiness": [
        "agentforce", "ai agent", "agent readiness", "copilot", "ai readiness",
        "agent exchange", "agentic", "agent-to-agent", "agent collaboration",
        "ai data readiness", "agent powered", "agent-driven",
    ],
    "data_pipelines": [
        "data cloud", "data 360", "data pipeline", "ingestion", "data volume",
        "consumption", "data stream", "streaming ingestion", "tableau",
        "real-time data", "real time data", "data source", "data flow",
        "data ingestion", "batch load", "data event",
    ],
    "config_technical_debt": [
        "technical debt", "configuration", "validation rule", "flow",
        "apex", "custom field", "config debt", "org health",
        "validation rules", "custom code", "apex trigger",
    ],
    "news_events": [
        "announce", "release", "update", "keynote", "dreamforce",
        "earnings", "downgrade", "upgrade", "forrester", "gartner",
        "rumor", "prediction", "conference",
    ],
    "workflow_redesign": [
        "workflow", "redesign", "process redesign", "job redesign",
        "role change", "operating model", "step-change", "step change",
        "work redesign", "human-in-the-loop", "human in the loop",
    ],
}

# How many posts to look back for the cooldown window
LOOKBACK_POSTS = 10
# How many posts back must have a different category (cooldown depth)
CATEGORY_COOLDOWN = 3  # If the same category appeared in any of the last 3 posts, block


def strip_em_dashes(text: str) -> str:
    """
    Replace all em-dash, en-dash, and similar Unicode dash characters
    with safe alternatives (regular hyphens, commas, or parentheses).

    This is a HARD filter - it runs on every LinkedIn post before posting.
    The LLM has repeatedly failed to self-police this rule.
    """
    for dash in DASH_CHARS:
        text = text.replace(dash, "-")
    
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
    
    Uses weighted scoring: more specific keywords (e.g., "matching rule")
    count more than generic ones (e.g., "data quality").
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


def fetch_recent_posts(channel_id: str, limit: int = 20) -> list[dict]:
    """
    Fetch the last N bot messages from a Discord channel via the REST API.
    Returns a list of dicts: {"content": str, "timestamp": str, "id": str}
    Filters out meta/cronjob response messages.
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
            posts = []
            for msg in messages:
                content = msg.get("content", "").strip()
                # Skip cronjob response messages and meta messages
                if content.startswith("Cronjob Response"):
                    continue
                if "Em-dash filter" in content or "- Length:" in content:
                    continue
                if len(content) < 50:
                    continue
                posts.append({
                    "content": content,
                    "timestamp": msg.get("timestamp", ""),
                    "id": msg.get("id", ""),
                })
            return posts
    except (json.JSONDecodeError, ValueError):
        pass
    
    return []


def check_topic_uniqueness(channel_id: str, proposed_text: str,
                           limit: int = LOOKBACK_POSTS) -> dict:
    """
    Check if the proposed post's topic category appeared too recently.
    
    Uses a cooldown window: if the same category appears in any of the last
    CATEGORY_COOLDOWN posts, the post is blocked. This prevents the same topic
    from appearing more than once within a ~1 week window (posts run 2x/week).
    
    If the topic IS similar to an older post (outside cooldown), suggests
    cross-referencing it to tie the two articles together.
    
    Returns:
        {
            "blocked": bool,
            "category": str,
            "recent_categories": list,   # Categories of last N posts (most recent first)
            "last_category": str,
            "similar_post": str | None,   # Content of a similar post outside cooldown
            "similar_post_date": str | None,
            "cross_ref_suggestion": str | None,
            "message": str,
        }
    """
    recent_posts = fetch_recent_posts(channel_id, limit)
    
    # Detect categories for recent posts
    recent_categories = []
    for post in recent_posts:
        cat = detect_category(post["content"])
        recent_categories.append({
            "category": cat,
            "timestamp": post["timestamp"],
            "content_preview": post["content"][:200],
        })
    
    proposed_category = detect_category(proposed_text)
    last_category = recent_categories[0]["category"] if recent_categories else "none"
    
    # Check cooldown: is the proposed category in the last CATEGORY_COOLDOWN posts?
    cooldown_posts = recent_categories[:CATEGORY_COOLDOWN]
    blocked = any(
        rc["category"] == proposed_category and proposed_category != "other"
        for rc in cooldown_posts
    )
    
    # Check for similar posts outside cooldown (for cross-referencing)
    similar_post = None
    similar_post_date = None
    cross_ref_suggestion = None
    for rc in recent_categories[CATEGORY_COOLDOWN:]:
        if rc["category"] == proposed_category and proposed_category != "other":
            similar_post = rc["content_preview"]
            similar_post_date = rc["timestamp"][:10]
            cross_ref_suggestion = (
                f"This topic appeared in a post on {similar_post_date}. "
                f"Consider referencing or building on that earlier post to tie "
                f"the two articles together. Earlier post opening: "
                f"\"{similar_post[:100]}...\""
            )
            break
    
    if blocked:
        blocking_cats = [rc["category"] for rc in cooldown_posts if rc["category"] == proposed_category]
        message = (
            f"BLOCKED: category '{proposed_category}' appeared in the last "
            f"{CATEGORY_COOLDOWN} posts. Must pick a different topic category. "
            f"Recent categories: {[rc['category'] for rc in recent_categories]}"
        )
    else:
        message = f"OK: proposed '{proposed_category}', recent: {[rc['category'] for rc in recent_categories]}"
        if cross_ref_suggestion:
            message += f". NOTE: {cross_ref_suggestion}"
    
    return {
        "blocked": blocked,
        "category": proposed_category,
        "recent_categories": [rc["category"] for rc in recent_categories],
        "last_category": last_category,
        "similar_post": similar_post,
        "similar_post_date": similar_post_date,
        "cross_ref_suggestion": cross_ref_suggestion,
        "message": message,
    }


# CLI for testing
if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="LinkedIn post filters")
    ap.add_argument("--test-dashes", action="store_true", help="Test em-dash stripping")
    ap.add_argument("--test-category", type=str, help="Test category detection on given text")
    ap.add_argument("--check-uniqueness", type=str, help="Check topic uniqueness (pass channel ID, read post from stdin)")
    ap.add_argument("--list-recent", type=str, help="List recent post categories (pass channel ID)")
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
    
    if args.list_recent:
        posts = fetch_recent_posts(args.list_recent, 10)
        for p in posts:
            cat = detect_category(p["content"])
            print(f'{p["timestamp"][:10]} [{cat}] {p["content"][:120]}...')
