#!/usr/bin/env python3
"""
linkedin_filters.py - HermesForge LinkedIn Post Filters (v2)

Programmatic guards for LinkedIn post quality and uniqueness:

  1. strip_em_dashes() — Replace all em-dash/en-dash chars
  2. check_topic_uniqueness() — Category-level cooldown (3-post window)
  3. check_semantic_adjacency() — Cross-category similarity detection (Option B)
     Catches posts that cross category boundaries but share the same semantic
     argument. If the new post would score highly on a SECONDARY category that
     is currently in the cooldown window, it's flagged as too similar.
  4. fingerprint_argument_structure() — Detects recycled narrative beats:
     problem → mechanism → consequence → root cause → solution → framing → close
     Returns a 7-tuple hash. Two posts with the same fingerprint are structurally
     identical even if the nouns change.
  5. --brief mode — Generates an article brief for the cron agent: recent posts,
     their categories, argument fingerprints, and audience targets. The agent
     reads this BEFORE writing so it can deliberately choose a different structure
     and focus.
  6. --full-check mode — Runs ALL checks (category, semantic adjacency, structural
     fingerprint) in one pass. Returns a single verdict with detailed reasoning.

Usage from cron:
  from linkedin_filters import full_quality_check, generate_article_brief
  brief = generate_article_brief(channel_id)
  result = full_quality_check(channel_id, proposed_text)
  if result["blocked"]:
      # pick a different topic and structural approach
"""

import re
import os
import json
import hashlib
import subprocess
import sys
from typing import Optional

# ── Dash filtering ──────────────────────────────────────────────────────────

EM_DASH = "\u2014"
EN_DASH = "\u2013"
HYPHEN = "\u2010"
FIGURE_DASH = "\u2012"
HORIZONTAL_BAR = "\u2015"
DASH_CHARS = [EM_DASH, EN_DASH, HYPHEN, FIGURE_DASH, HORIZONTAL_BAR]


def strip_em_dashes(text: str) -> str:
    for dash in DASH_CHARS:
        text = text.replace(dash, "-")
    text = text.replace("&mdash;", "-")
    text = text.replace("&ndash;", "-")
    text = text.replace("&#8212;", "-")
    text = text.replace("&#8211;", "-")
    return text


def verify_no_dashes(text: str) -> bool:
    for dash in DASH_CHARS:
        if dash in text:
            return False
    return True


# ── Category detection (keyword-weighted scoring) ──────────────────────────

TOPIC_CATEGORIES = {
    "duplicate_data": [
        "duplicate", "duplicates", "dedup", "deduplication", "duplicate record",
        "data quality", "matching rule", "match rule", "duplicate rule",
        "duplicate record set", "duplicate management", "duplicate check",
        "record merge", "data deduplication", "duplicate detection",
        "data cleanup", "data steward", "data stewardship",
    ],
    "digital_transformation": [
        "digital transformation", "modernization", "legacy", "transformation",
        "legacy migration", "legacy system",
    ],
    "ai_agent_readiness": [
        "agentforce", "ai agent", "agent readiness", "copilot", "ai readiness",
        "agent exchange", "agentic", "agent-to-agent", "agent collaboration",
        "ai data readiness", "agent powered", "agent-driven",
        "ai-powered", "ai powered", "agent strategy", "clean core for ai",
        "trusted context", "identity resolution", "unified profile",
    ],
    "data_pipelines": [
        "data cloud", "data 360", "data pipeline", "ingestion", "data volume",
        "consumption", "data stream", "streaming ingestion", "tableau",
        "real-time data", "real time data", "data source", "data flow",
        "data ingestion", "batch load", "data event", "data architecture",
        "data fabric", "data lake", "data warehouse", "data strategy",
    ],
    "config_technical_debt": [
        "technical debt", "configuration", "validation rule", "flow",
        "apex", "custom field", "config debt", "org health",
        "validation rules", "custom code", "apex trigger",
        "automated testing", "regression test", "deployment",
        "metadata", "sandbox", "change set", "devops",
    ],
    "news_events": [
        "announce", "release", "update", "keynote", "dreamforce",
        "earnings", "downgrade", "upgrade", "forrester", "gartner",
        "rumor", "prediction", "conference", "acquisition",
    ],
    "workflow_redesign": [
        "workflow", "redesign", "process redesign", "job redesign",
        "role change", "operating model", "step-change", "step change",
        "work redesign", "human-in-the-loop", "human in the loop",
        "platform of action", "operating model", "org design",
    ],
    "enterprise_agentic_ai": [
        "enterprise ai", "agent orchestration", "multi-agent", "agent swarm",
        "autonomous agent", "agent deployment", "llm operations", "llm ops",
        "model selection", "model routing", "model tier", "cost optimization",
        "prompt engineering", "rag", "retrieval augmented generation",
        "knowledge graph", "vector database", "ai governance",
        "ai guardrails", "ai safety", "hallucination", "ai accuracy",
        "reasoning model", "tool use", "function calling", "api agent",
        "autonomous workflow", "agent ecosystem", "agent platform",
    ],
    "salesforce_obscure": [
        "obscure", "hidden gem", "did you know", "less known", "overlooked",
        "underrated", "little-known", "hidden feature", "power user",
        "pro tip", "expert tip", "insider", "uncommon", "rarely used",
        "secret", "trick", "hack", "shortcut", "easter egg",
        "undocumented", "not in the manual",
    ],
}

# Categories that are semantically adjacent — posts in different primary
# categories that share the same underlying argument are flagged as similar.
# Format: (category_A, category_B) — order doesn't matter.
SEMANTIC_ADJACENCY = [
    ("duplicate_data", "ai_agent_readiness"),     # both about "dirty data → AI fails"
    ("ai_agent_readiness", "data_pipelines"),     # both about "data infrastructure for AI"
    ("ai_agent_readiness", "enterprise_agentic_ai"),  # both about AI agents, different lens
    ("duplicate_data", "data_pipelines"),         # both about "data quality and flow"
    ("workflow_redesign", "digital_transformation"),  # both about org change
    ("config_technical_debt", "workflow_redesign"),   # both about fixing legacy
    ("salesforce_obscure", "config_technical_debt"),  # obscure features often in config space
]

# How many posts to look back
LOOKBACK_POSTS = 10
# Cooldown: same category can't appear in any of the last N posts
CATEGORY_COOLDOWN = 3


def detect_category(text: str) -> str:
    text_lower = text.lower()
    scores = {}
    for category, keywords in TOPIC_CATEGORIES.items():
        score = sum(1 for kw in keywords if kw in text_lower)
        if score > 0:
            scores[category] = score
    if scores:
        return max(scores.items(), key=lambda x: x[1])[0]
    return "other"


def detect_all_category_scores(text: str) -> dict:
    """Return ALL category scores, not just the winning one.
    Used for semantic adjacency detection."""
    text_lower = text.lower()
    scores = {}
    for category, keywords in TOPIC_CATEGORIES.items():
        score = sum(1 for kw in keywords if kw in text_lower)
        scores[category] = score
    return scores


def _adjacent_categories(cat: str) -> set:
    """Return set of categories semantically adjacent to `cat`."""
    adjacent = set()
    for a, b in SEMANTIC_ADJACENCY:
        if a == cat:
            adjacent.add(b)
        elif b == cat:
            adjacent.add(a)
    return adjacent


# ── Argument structure fingerprinting ───────────────────────────────────────
#
# Detects whether two posts use the same narrative skeleton:
#   problem → mechanism → consequence → root_cause → solution → framing → close
#
# Each beat is detected by keyword patterns. The fingerprint is a hash of the
# 7-element presence vector — two posts with identical structure produce the
# same hash even if the topic nouns differ.

STRUCTURE_BEATS = {
    "problem": [
        r"problem", r"issue", r"challenge", r"struggling", r"gap",
        r"doesn't work", r"fails", r"broken", r"wrong", r"miss",
        r"wall", r"hitting a wall", r"can't", r"won't", r"frustrat",
    ],
    "mechanism": [
        r"here'?s (what|how|why)", r"here is (what|how|why)",
        r"what (happens|actually)|the way it works|under the hood",
        r"in practice", r"in real", r"silently", r"behind the scenes",
        r"this is how", r"the mechanism", r"the logic",
    ],
    "consequence": [
        r"result", r"outcome", r"consequence", r"impact",
        r"downstream", r"ripple", r"cascade", r"this means",
        r"which means", r"so (the|your|that)", r"end up",
        r"leaving", r"creating", r"producing",
    ],
    "root_cause": [
        r"root cause", r"underlying", r"because", r"why does",
        r"the reason", r"at the core", r"fundamental",
        r"not about", r"it's not", r"the real (issue|problem)",
    ],
    "solution": [
        r"solution", r"fix", r"approach", r"what to do",
        r"how to (fix|solve|address)", r"here'?s (what|how)",
        r"the answer", r"resolv", r"treat(ing)? (it|this)",
        r"requires", r"step", r"process", r"pipeline",
        r"tool", r"platform", r"recurring", r"automated",
    ],
    "framing": [
        r"we call (it|this)", r"branded", r"trademark", r"\(TM\)",
        r"coined", r"term", r"label", r"concept",
        r"framework", r"methodology", r"philosophy",
        r"mental model", r"way of thinking",
    ],
    "close": [
        r"this is solvable", r"the real shift", r"bottom line",
        r"here'?s the thing", r"treat(ing)? (this|it) (as|like)",
        r"requires treating", r"comes down to",
        r"at the end of the day", r"in the end",
        r"what matters", r"the takeaway",
    ],
}


def fingerprint_argument_structure(text: str) -> str:
    """Return a 7-character hex fingerprint of the argument structure.

    Identical structure = identical fingerprint, regardless of topic."""
    text_lower = text.lower()
    vector = []
    for beat_name, patterns in STRUCTURE_BEATS.items():
        present = any(re.search(p, text_lower) for p in patterns)
        vector.append("1" if present else "0")
    vec_str = "".join(vector)
    return hashlib.md5(vec_str.encode()).hexdigest()[:7]


def _detect_structure_beats_present(text: str) -> list:
    """Return list of structure beat names detected in the text."""
    text_lower = text.lower()
    present = []
    for beat_name, patterns in STRUCTURE_BEATS.items():
        if any(re.search(p, text_lower) for p in patterns):
            present.append(beat_name)
    return present


# ─ Discord API ─────────────────────────────────────────────────────────────────

def fetch_recent_posts(channel_id: str, limit: int = 20) -> list[dict]:
    """Fetch the last N bot messages from a Discord channel.

    Returns list of dicts: {content, timestamp, id}.
    Filters out meta/cronjob response messages."""
    token = os.environ.get("DISCORD_BOT_TOKEN", "")
    if not token:
        print("WARNING: DISCORD_BOT_TOKEN not set", file=sys.stderr)
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


# ── Core quality checks ────────────────────────────────────────────────────

def check_topic_uniqueness(channel_id: str, proposed_text: str,
                           limit: int = LOOKBACK_POSTS) -> dict:
    """Category-level cooldown check. Same category within last 3 posts = blocked."""
    recent_posts = fetch_recent_posts(channel_id, limit)
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
    cooldown_posts = recent_categories[:CATEGORY_COOLDOWN]
    blocked = any(
        rc["category"] == proposed_category and proposed_category != "other"
        for rc in cooldown_posts
    )

    similar_post = None
    similar_post_date = None
    cross_ref_suggestion = None
    for rc in recent_categories[CATEGORY_COOLDOWN:]:
        if rc["category"] == proposed_category and proposed_category != "other":
            similar_post = rc["content_preview"]
            similar_post_date = rc["timestamp"][:10]
            cross_ref_suggestion = (
                f"This topic appeared in a post on {similar_post_date}. "
                f"Build on that earlier post rather than repeating."
            )
            break

    if blocked:
        message = (
            f"BLOCKED: category '{proposed_category}' in last {CATEGORY_COOLDOWN} posts. "
            f"Recent: {[rc['category'] for rc in recent_categories]}"
        )
    else:
        message = f"OK: '{proposed_category}', recent: {[rc['category'] for rc in recent_categories]}"
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


def check_semantic_adjacency(channel_id: str, proposed_text: str,
                              limit: int = LOOKBACK_POSTS) -> dict:
    """Cross-category semantic check (Option B).

    Even if the PRIMARY category is different, checks whether the post scores
    highly on a SECONDARY category that IS in the cooldown window AND is
    semantically adjacent to the primary. Catches posts that change the
    Salesforce feature name but reuse the same argument."""
    recent_posts = fetch_recent_posts(channel_id, limit)

    proposed_scores = detect_all_category_scores(proposed_text)
    primary = detect_category(proposed_text)

    cooldown_cats = set()
    for post in recent_posts[:CATEGORY_COOLDOWN]:
        cooldown_cats.add(detect_category(post["content"]))

    adjacent_blocked = []
    for cat, score in proposed_scores.items():
        if cat == primary:
            continue
        if score < 2:
            continue
        if cat in cooldown_cats:
            adjacent = _adjacent_categories(primary)
            if cat in adjacent or primary in _adjacent_categories(cat):
                adjacent_blocked.append(cat)

    if adjacent_blocked:
        secondary = adjacent_blocked[0]
        message = (
            f"SEMANTIC WARNING: primary='{primary}', but text also scores on "
            f"'{secondary}' (score={proposed_scores.get(secondary, 0)} keywords) "
            f"which IS in cooldown. Categories '{primary}' and '{secondary}' "
            f"are semantically adjacent. The argument may be too similar."
        )
    else:
        message = f"OK: no semantic adjacency conflict. Primary={primary}"

    return {
        "semantically_similar": len(adjacent_blocked) > 0,
        "primary": primary,
        "secondary_scores": {k: v for k, v in proposed_scores.items() if v >= 2 and k != primary},
        "adjacent_blocked": adjacent_blocked,
        "cooldown_categories": sorted(cooldown_cats),
        "message": message,
    }

def generate_article_brief(channel_id: str, limit: int = LOOKBACK_POSTS) -> str:
    """Generate an article brief for the cron agent before writing.

    Summarizes recent posts: categories, argument structures, audience targets.
    The agent reads this BEFORE writing so it can deliberately choose a
    different structure and focus."""
    recent = fetch_recent_posts(channel_id, limit)

    if not recent:
        return "No recent posts found in channel."

    lines = [
        "## Article Brief - Recent LinkedIn Posts",
        "",
        f"Last {len(recent)} posts (most recent first):",
        "",
    ]

    for i, post in enumerate(recent):
        cat = detect_category(post["content"])
        fp = fingerprint_argument_structure(post["content"])
        beats = _detect_structure_beats_present(post["content"])
        word_count = len(post["content"].split())
        opening = post["content"][:150].replace("\n", " ")

        lines.append(f"### Post {i+1} - {post['timestamp'][:10]} - [{cat}] - {word_count} words")
        lines.append(f"Structure fingerprint: `{fp}`")
        lines.append(f"Beats detected: {', '.join(beats) if beats else 'none'}")
        lines.append(f"Opening: {opening}...")
        lines.append("")

    # Summary
    cats_seen = []
    fps_seen = []
    for post in recent[:3]:
        cat = detect_category(post["content"])
        fp = fingerprint_argument_structure(post["content"])
        if cat not in cats_seen:
            cats_seen.append(cat)
        if fp not in fps_seen:
            fps_seen.append(fp)

    lines.append("## Diversity Guidance")
    lines.append("")
    lines.append(f"**Categories in cooldown:** {', '.join(cats_seen)}")
    lines.append(f"**Structure fingerprints used:** {', '.join(fps_seen)}")
    lines.append("")
    lines.append("**DO NOT reuse:** any fingerprint or category listed above.")
    lines.append("**DO vary:** argument structure, audience target, focus area.")

    return "\n".join(lines)

def full_quality_check(channel_id: str, proposed_text: str,
                       limit: int = LOOKBACK_POSTS) -> dict:
    """Run all quality checks in one pass.

    Returns: {blocked: bool, reasons: list[str], details: dict}"""
    reasons = []
    details = {}

    # 1. Category cooldown
    uniqueness = check_topic_uniqueness(channel_id, proposed_text, limit)
    details["uniqueness"] = uniqueness
    if uniqueness["blocked"]:
        reasons.append(f"CATEGORY_COOLDOWN: {uniqueness['message']}")

    # 2. Semantic adjacency (Option B)
    adjacency = check_semantic_adjacency(channel_id, proposed_text, limit)
    details["adjacency"] = adjacency
    if adjacency["semantically_similar"]:
        reasons.append(f"SEMANTIC_ADJACENCY: {adjacency['message']}")

    # 3. Structure fingerprint
    fp = fingerprint_argument_structure(proposed_text)
    recent = fetch_recent_posts(channel_id, CATEGORY_COOLDOWN)
    recent_fps = [fingerprint_argument_structure(p["content"]) for p in recent]
    structure_repeated = fp in recent_fps
    details["fingerprint"] = {"current": fp, "recent": recent_fps, "repeated": structure_repeated}
    if structure_repeated:
        reasons.append(f"STRUCTURE_REPEAT: fingerprint {fp} already in last {CATEGORY_COOLDOWN} posts")

    return {
        "blocked": len(reasons) > 0,
        "reasons": reasons,
        "details": details,
        "message": "; ".join(reasons) if reasons else "PASS - all checks passed",
    }
