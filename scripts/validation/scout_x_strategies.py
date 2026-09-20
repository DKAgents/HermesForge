#!/usr/bin/env python3
"""
X Strategy Scout — nightly crawl for trading strategy patterns on X.
Phase 1: search → score from snippets → read top candidates → write HYP notes.

Scoring: keyword + structure heuristics (0-100 scale).
Threshold: >= 50 → candidate, >= 70 → auto-HYP.

Usage: python3 scout_x_strategies.py [--dry-run] [--max-candidates N] [--threshold N]
"""

import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# ── Config ──────────────────────────────────────────────────────────────

SEARCH_QUERIES = [
    "win rate setup backtest",
    "trading edge strategy setup",
    "backtest results profit factor",
    "ICT trading strategy",
    "SMC entry model strategy",
    "swing trade setup rules",
    "breakout reversal strategy thread",
]

MAX_SEARCH_RESULTS = 10          # per query
MAX_CANDIDATE_READS = 8          # total posts to full-read across all queries
DEFAULT_THRESHOLD = 50           # minimum score to flag as candidate
AUTO_HYP_THRESHOLD = 40          # score to auto-generate HYP note (lower than search threshold since full-read adds context)
MAX_CANDIDATES = 5               # max HYP notes per run

PROJECT_ROOT = Path("/root/HermesForge")
HYP_DIR = PROJECT_ROOT / "06-Strategies" / "Hypotheses"
FORGE_DIR = PROJECT_ROOT / "04-ForgeLoop"
SOURCES_SCRIPT = Path("/root/.hermes/skills/research/grounded-citations/scripts/sources.py")

# ── Scoring ─────────────────────────────────────────────────────────────

ENTRY_KEYWORDS = [
    r"\bentry\b", r"\bbuy\b.*\bwhen\b", r"\blong\b.*\bcondition\b",
    r"\bcross(?:es|ing|ed)?\b.*\babove\b", r"\bRSI\b.*\b(?:below|under)\b",
    r"\bMACD\b", r"\bSMA\b.*\bcross", r"\bpullback\b.*\bentry\b",
    r"\bbreakout\b.*\bentry\b", r"\breversal\b.*\bentry\b",
    r"\bFVG\b", r"\bOB\b", r"\bbreaker\b", r"\bliquidity\b.*\bsweep\b",
    r"\bChoCH\b", r"\bBOS\b", r"\bmitigation\b",
    # Broader signals — give partial credit
    r"\bsetup\b", r"\bpattern\b", r"\bstrategy\b",
    r"\bEMA\d*\s*(?:cross|above|below)", r"\bMA\s*cross",
    r"\b(?:buy|long|short)\b.*\b(?:signal|trigger)\b",
    r"\binside\s*bar\b", r"\bengulfing\b", r"\bdoji\b",
    r"\bpin\s*bar\b", r"\bhammer\b", r"\bdouble\s*(?:top|bottom)\b",
]

EXIT_KEYWORDS = [
    r"\bexit\b", r"\bstop\b.*\bloss\b", r"\btake\b.*\bprofit\b",
    r"\btarget\b", r"\bTP\d?\b", r"\bSL\b", r"\btrailing\b.*\bstop\b",
    r"\brisk\b.*\breward\b", r"\bR:R\b", r"\bATR\b.*\bstop\b",
    r"\btime\b.*\bstop\b", r"\bclose\b.*\bposition\b",
]

RESULTS_KEYWORDS = [
    r"\bwin\b.*\brate\b.*\d{1,2}[%％]", r"\b(?:win|hit)\b.*\brate\b",
    r"\bprofit\b.*\bfactor\b.*\d+\.?\d*", r"\bsharpe\b.*\d+\.?\d*",
    r"\b(?:avg|average)\b.*\b(?:return|gain|R)\b",
    r"\bbacktest\b", r"\bout.?of.?sample\b", r"\bwalk.?forward\b",
    r"\b\d+[%％]\s*win", r"\b(?:PF|SQN)\b.*\d+",
]

SPECIFICITY_KEYWORDS = [
    r"\b(?:SPY|QQQ|IWM|DIA|AAPL|MSFT|NVDA|TSLA|BTC|ETH|SOL)\b",
    r"\b(?:daily|weekly|4hr?|1hr?|5min|15min|30min)\b.*\b(?:chart|timeframe|TF)\b",
    r"\b(?:stocks?|crypto|forex|futures|equities)\b",
    r"\b(?:swing|day|scalp)\b.*\btrad(?:e|ing)\b",
    r"\b\d+\s*(?:trades?|signals?)\b",
]

THREAD_INDICATORS = [
    r"\bthread\b", r"\b🧵\b", r"\(?\d+/\d+\)?", r"\bpart\b.*\b\d+\b",
    r"\bdetailed\b.*\b(?:below|thread|breakdown)\b",
    r"\bfollow\b.*\b(?:up|thread)\b",
]


def score_tweet(text: str) -> tuple[int, dict]:
    """Score a tweet for strategy-like content. Returns (score, breakdown)."""
    text_lower = text.lower()
    breakdown = {}

    entry_hits = sum(1 for kw in ENTRY_KEYWORDS if re.search(kw, text_lower))
    entry_score = min(30, entry_hits * 8)
    breakdown["entry"] = entry_score

    exit_hits = sum(1 for kw in EXIT_KEYWORDS if re.search(kw, text_lower))
    exit_score = min(25, exit_hits * 6)
    breakdown["exit"] = exit_score

    results_hits = sum(1 for kw in RESULTS_KEYWORDS if re.search(kw, text_lower))
    results_score = min(20, results_hits * 7)
    breakdown["results"] = results_score

    spec_hits = sum(1 for kw in SPECIFICITY_KEYWORDS if re.search(kw, text_lower))
    spec_score = min(15, spec_hits * 5)
    breakdown["specificity"] = spec_score

    thread_hits = sum(1 for kw in THREAD_INDICATORS if re.search(kw, text_lower))
    thread_score = min(10, thread_hits * 5)
    breakdown["thread"] = thread_score

    total = entry_score + exit_score + results_score + spec_score + thread_score
    return total, breakdown


def extract_strategy_spec(text: str) -> dict:
    """Extract strategy parameters from tweet text using heuristics."""
    spec = {"entry": [], "exit": [], "results": {}, "timeframe": None, "instruments": []}

    # Timeframe
    tf_match = re.search(
        r"\b(daily|weekly|4hr?|1hr?|5\s*min|15\s*min|30\s*min|1\s*min)\b",
        text, re.IGNORECASE
    )
    if tf_match:
        spec["timeframe"] = tf_match.group(1).lower()

    # Instruments
    for ticker in ["SPY", "QQQ", "IWM", "DIA", "AAPL", "MSFT", "NVDA", "TSLA",
                    "BTC", "ETH", "SOL", "AVAX", "LINK"]:
        if re.search(rf"\b{ticker}\b", text):
            spec["instruments"].append(ticker)

    # Entry conditions — capture sentences near entry keywords (expanded for natural language)
    entry_sentences = re.findall(
        r"[^.!?\n]{0,200}\b(?:entry|buy|long|signal|cross|crossover|trigger"
        r"|setup|pattern|breakout|reversal|pullback|sweep|breaker|mitigation"
        r"|inside\s*bar|engulfing|doji|hammer|pin\s*bar"
        r"|condition|rule|criterion|filter|check|confirmation"
        r"|buy\b|sell\b|open\b)(?:\s|ing|s|ed)?\b[^.!?\n]{0,200}",
        text, re.IGNORECASE
    )
    spec["entry"] = [s.strip()[:120] for s in entry_sentences[:3]]

    # Exit conditions — expanded for natural language
    exit_sentences = re.findall(
        r"[^.!?\n]{0,200}\b(?:exit|stop|target|take[- ]?profit|TP\d?|SL"
        r"|close\b|sell\b|cover\b|liquidate|flat"
        r"|trailing|reverse|opposite|crossover|EMA\s*cross"
        r"|risk|ATR|time\s*stop|invalidation)(?:\s|ing|s|ed)?\b[^.!?\n]{0,200}",
        text, re.IGNORECASE
    )
    spec["exit"] = [s.strip()[:120] for s in exit_sentences[:3]]

    # Win rate
    wr_match = re.search(r"(\d{1,3})\s*[%％]\s*win", text, re.IGNORECASE)
    if wr_match:
        spec["results"]["win_rate"] = int(wr_match.group(1))

    # Profit factor
    pf_match = re.search(r"profit\s*factor\s*[:=]?\s*(\d+\.?\d*)", text, re.IGNORECASE)
    if pf_match:
        spec["results"]["profit_factor"] = float(pf_match.group(1))

    return spec


# ── X API via xurl ──────────────────────────────────────────────────────

def xurl_search(query: str, n: int = 10) -> list[dict]:
    """Run xurl search, return list of tweet dicts."""
    try:
        result = subprocess.run(
            ["xurl", "search", query, "-n", str(n)],
            capture_output=True, text=True, timeout=15
        )
        if result.returncode != 0:
            print(f"  ⚠ xurl search failed: {result.stderr[:200]}", file=sys.stderr)
            return []
        data = json.loads(result.stdout)
        # xurl returns {data: [...]} or {data: [{...}]} structure
        if isinstance(data, dict) and "data" in data:
            tweets = data["data"]
            if isinstance(tweets, list):
                return tweets
        return []
    except (json.JSONDecodeError, subprocess.TimeoutExpired) as e:
        print(f"  ⚠ xurl search error: {e}", file=sys.stderr)
        return []


def xurl_read(post_id: str) -> Optional[dict]:
    """Read a single tweet by ID."""
    try:
        result = subprocess.run(
            ["xurl", "read", post_id],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode != 0:
            return None
        data = json.loads(result.stdout)
        if isinstance(data, dict) and "data" in data:
            return data["data"]
        return None
    except (json.JSONDecodeError, subprocess.TimeoutExpired):
        return None


def xurl_thread_context(post_id: str, author_username: str, max_replies: int = 3) -> str:
    """Fetch a few replies from the same author to build thread context."""
    # Search for replies by the same author to their own post
    query = f"from:{author_username} to:{author_username}"
    try:
        result = subprocess.run(
            ["xurl", "search", query, "-n", str(max_replies)],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode != 0:
            return ""
        data = json.loads(result.stdout)
        if isinstance(data, dict) and "data" in data:
            tweets = data["data"]
            if isinstance(tweets, list):
                return "\n".join(t.get("text", "") for t in tweets[:max_replies])
    except Exception:
        pass
    return ""


# ── Vault Integration ────────────────────────────────────────────────────

def get_next_hyp_id(counter: list[int]) -> str:
    """Find and increment the next available HYP number. Pass a mutable counter list for in-run tracking."""
    if not counter:
        # First call: seed from disk
        max_hyp = 0
        if HYP_DIR.exists():
            for f in HYP_DIR.iterdir():
                if f.suffix == ".md":
                    text = f.read_text()
                    for m in re.finditer(r"HYP-(\d+)", text):
                        max_hyp = max(max_hyp, int(m.group(1)))
        counter.append(max_hyp + 1)
    else:
        counter[0] += 1
    return f"HYP-{counter[0]}"


def write_hyp_note(candidate: dict, hyp_id: str) -> Path:
    """Write a Hypothesis note to the vault."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    slug = candidate.get("title", "x-scout-strategy").lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)[:60].strip("-")
    filename = f"STR-{today}-{slug}.md"
    filepath = HYP_DIR / filename

    spec = candidate.get("spec", {})
    entry_text = "\n".join(f"- {e}" for e in spec.get("entry", [])) or "- (see source)"
    exit_text = "\n".join(f"- {e}" for e in spec.get("exit", [])) or "- (see source)"
    instruments = ", ".join(spec.get("instruments", [])) or "TBD"
    tf = spec.get("timeframe", "TBD")
    wr = spec.get("results", {}).get("win_rate", None)
    pf = spec.get("results", {}).get("profit_factor", None)

    results_block = ""
    if wr:
        results_block += f"- Reported win rate: {wr}%\n"
    if pf:
        results_block += f"- Reported profit factor: {pf}\n"

    content = f"""---
id: STR-{today}-{slug}
type: strategy
status: hypothesis
asset_class: TBD
venue: TBD
trade_style: TBD
timeframe: {tf}
confidence: low
last_reviewed: {today}
hypothesis_id: {hyp_id}
source: "@{candidate.get('username', 'unknown')}"
source_url: "{candidate.get('url', '')}"
scout_score: {candidate.get('score', 0)}
scout_date: {today}
gates_passed: []
eligible_assets: []
---

# {candidate.get('title', 'Untitled Strategy')} ({hyp_id})

## Thesis

{candidate.get('thesis', '(Extracted from X — see source for full context)')}

## Source

{candidate.get('source_text', '')[:500]}

## Entry Criteria

{entry_text}

## Exit Criteria

{exit_text}

## Reported Results

{results_block or '- No backtest results shared in post'}

## Instruments

{instruments}

## Gauntlet Status

- G0: Not yet run
- G3: Not yet run
- Next step: Write scanner, run Phase 1a backtest

---
*Sourced by X Strategy Scout on {today}*
"""
    filepath.write_text(content)
    return filepath


def write_scout_report(candidates: list[dict], queries_run: int, total_read: int) -> Path:
    """Write daily scout report."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    filepath = FORGE_DIR / f"X-SCOUT-{today}.md"

    lines = [
        f"# X Strategy Scout — {today}",
        "",
        f"**Queries run:** {queries_run}",
        f"**Posts read:** {total_read}",
        f"**Candidates found:** {len(candidates)}",
        "",
        "---",
        "",
    ]

    if not candidates:
        lines.append("No strategy candidates found today.")
    else:
        for i, c in enumerate(candidates, 1):
            lines.extend([
                f"## Candidate {i}: {c.get('title', 'Untitled')}",
                f"- **Score:** {c.get('score', 0)}/100",
                f"- **Source:** [{c.get('username', 'unknown')}]({c.get('url', '')})",
                f"- **HYP ID:** {c.get('hyp_id', 'N/A')}",
                f"- **File:** {c.get('file', 'N/A')}",
                "",
                f"**Thesis:** {c.get('thesis', 'N/A')}",
                "",
            ])

    filepath.write_text("\n".join(lines))
    return filepath


# ── Main ─────────────────────────────────────────────────────────────────

def main(dry_run: bool = False, max_candidates: int = MAX_CANDIDATES,
         threshold: int = DEFAULT_THRESHOLD, priority_file: str = ""):
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    print(f"🔍 X Strategy Scout — {today}")
    print(f"   Threshold: {threshold}, Max candidates: {max_candidates}")
    if dry_run:
        print("   🧪 DRY RUN — no files will be written")
    if priority_file:
        print(f"   📎 Priority file: {priority_file}")
    print()

    # Phase 0: Deep-read priority URLs from Edge Discovery
    priority_tweets = []
    if priority_file:
        pf = Path(priority_file)
        if pf.exists():
            urls = [l.split("#")[0].strip() for l in pf.read_text().split('\n')
                    if l.strip() and 'x.com/' in l and '/status/' in l]
            print(f"  📎 Edge Discovery candidates: {len(urls)} URLs")
            for url in urls[:8]:  # cap at 8 deep-reads
                post_id = url.rstrip('/').split('/status/')[-1].split('?')[0]
                if post_id.isdigit():
                    full = xurl_read(post_id)
                    if full and full.get("text"):
                        full["_query"] = "edge-discovery"
                        full["_priority"] = True
                        priority_tweets.append(full)
                        print(f"    ✅ Deep-read: {post_id}")
            print()

    # Phase 1: Search + score from snippets
    all_tweets = []  # (tweet_dict, query)

    for query in SEARCH_QUERIES:
        print(f"  Searching: {query[:70]}...")
        tweets = xurl_search(query, n=MAX_SEARCH_RESULTS)
        print(f"    → {len(tweets)} results")
        for tweet in tweets:
            tweet["_query"] = query
        all_tweets.extend(tweets)

    # Deduplicate by ID, priority tweets override search results
    seen = set()
    unique_tweets = []
    for t in priority_tweets:  # priority first
        tid = t.get("id")
        if tid and tid not in seen:
            seen.add(tid)
            unique_tweets.append(t)
    for t in all_tweets:
        tid = t.get("id")
        if tid and tid not in seen:
            seen.add(tid)
            unique_tweets.append(t)

    print(f"\n  Deduplicated: {len(unique_tweets)} unique tweets "
          f"(+{len(priority_tweets)} priority)\n")

    # Score each tweet
    scored = []
    for tweet in unique_tweets:
        text = tweet.get("text", "")
        score, breakdown = score_tweet(text)
        is_priority = tweet.get("_priority", False)
        if score >= threshold or is_priority:
            scored.append((score, breakdown, tweet))

    # Sort: priority tweets first, then by score
    scored.sort(key=lambda x: (not x[2].get("_priority", False), -x[0]))
    print(f"  Scored >= {threshold}: {len(scored)} candidates")
    for score, bd, tw in scored[:10]:
        author = tw.get("author_id", "?")
        snippet = tw.get("text", "")[:80].replace("\n", " ")
        print(f"    [{score:3d}] {snippet}...")

    if not scored:
        print("\n  No candidates found.")
        return

    # Phase 2: Full-read top candidates for rich extraction
    top_scored = scored[:MAX_CANDIDATE_READS]
    candidates = []
    hyp_counter: list[int] = []  # mutable counter for in-run HYP ID tracking

    for score, breakdown, tweet in top_scored:
        post_id = tweet.get("id")
        if not post_id:
            continue

        print(f"\n  📖 Reading post {post_id} (score {score})...")
        full = xurl_read(post_id)
        if not full:
            print("    ⚠ Could not read full post")
            continue

        full_text = full.get("text", tweet.get("text", ""))

        # Try to get thread context
        author_username = full.get("author", {}).get("username", "") if isinstance(full.get("author"), dict) else ""
        if not author_username:
            author_username = full.get("username", "")

        # Score the full text (may be different from snippet)
        full_score, full_bd = score_tweet(full_text)

        if full_score >= threshold or score >= threshold:
            spec = extract_strategy_spec(full_text)
            hyp_id = get_next_hyp_id(hyp_counter)

            # Build candidate
            candidate = {
                "score": full_score or score,
                "title": spec.get("entry", [full_text[:80]])[0][:80] if spec.get("entry") else full_text[:80],
                "username": author_username or tweet.get("author_id", "unknown"),
                "url": f"https://x.com/{author_username}/status/{post_id}" if author_username else f"https://x.com/i/status/{post_id}",
                "source_text": full_text,
                "thesis": full_text[:300],
                "spec": spec,
                "hyp_id": hyp_id,
            }

            if full_score >= AUTO_HYP_THRESHOLD or score >= AUTO_HYP_THRESHOLD:
                if not dry_run and len(candidates) < max_candidates:
                    filepath = write_hyp_note(candidate, hyp_id)
                    candidate["file"] = str(filepath)
                    print(f"    ✅ Auto-HYP: {hyp_id} → {filepath.name}")
                else:
                    candidate["file"] = "(dry-run, not written)"

            candidates.append(candidate)

        if len(candidates) >= max_candidates:
            break

    # Phase 3: Write report
    print(f"\n  📝 Candidates: {len(candidates)}")
    if not dry_run and candidates:
        report_path = write_scout_report(candidates, len(SEARCH_QUERIES), len(top_scored))
        print(f"  📄 Report: {report_path}")

    if dry_run:
        print("\n  🧪 Dry run complete — no files written.")
    else:
        print("\n  ✅ Scout complete.")


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    max_candidates = MAX_CANDIDATES
    threshold = DEFAULT_THRESHOLD
    priority_file = ""

    for i, arg in enumerate(sys.argv):
        if arg == "--max-candidates" and i + 1 < len(sys.argv):
            max_candidates = int(sys.argv[i + 1])
        if arg == "--threshold" and i + 1 < len(sys.argv):
            threshold = int(sys.argv[i + 1])
        if arg.startswith("--priority-file="):
            priority_file = arg.split("=", 1)[1]
        elif arg == "--priority-file" and i + 1 < len(sys.argv):
            priority_file = sys.argv[i + 1]

    main(dry_run=dry_run, max_candidates=max_candidates,
         threshold=threshold, priority_file=priority_file)