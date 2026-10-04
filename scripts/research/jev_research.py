#!/usr/bin/env python3
"""
JEV Browser Research Pipeline
==============================
Combines browser content extraction with JEV classification for fast
research triage. Use when you need to evaluate many sources quickly.

Modes:
  --url URL         Classify a single URL
  --search QUERY    Search + classify top N results
  --classify TEXT   Classify raw text without fetching

Examples:
  python3 jev_research.py --url "https://coindesk.com/article" --quick
  python3 jev_research.py --search "ETH ETF inflows October 2026" --depth 3
  python3 jev_research.py --classify "$(cat article.txt)" --questions custom.json
"""
import argparse
import json
import sys
import time
from pathlib import Path
from typing import Optional
from urllib.request import urlopen, Request
from urllib.error import URLError

# Add gauntlet to path for JevClient
_gauntlet = Path(__file__).resolve().parent.parent / "gauntlet"
sys.path.insert(0, str(_gauntlet))
from jev_client import JevClient, JevError

# ── Default research questions ──

DEFAULT_QUESTIONS = {
    "relevance": {
        "type": "noul",
        "instructions": "Is this content relevant to cryptocurrency/blockchain markets or macro finance?",
        "true_criteria": "Discusses crypto markets, DeFi, blockchain tech, regulation, macro drivers, or institutional adoption",
        "false_criteria": "Unrelated general news, lifestyle, entertainment, or non-financial topics"
    },
    "depth": {
        "type": "score",
        "instructions": "Rate the analytical depth of this content",
        "levels": [
            "superficial — headline-only, no analysis",
            "shallow — some context but mostly repackaging",
            "moderate — original analysis with supporting data",
            "deep — novel thesis, quantitative backing, contrarian angle",
            "expert — institutional-grade research, primary sources, tradeable edge"
        ]
    },
    "bias": {
        "type": "choice",
        "instructions": "What is the dominant market bias of this content?",
        "options": {
            "bullish": "Optimistic, expects prices to rise",
            "bearish": "Pessimistic, expects prices to fall",
            "neutral": "Balanced, presents both sides",
            "uncertain": "Mixed signals, unclear direction",
            "meta": "Not about market direction (regulation, tech, etc.)"
        }
    },
    "actionable": {
        "type": "noul",
        "instructions": "Does this content contain actionable trading or investment insights?",
        "true_criteria": "Specific levels, timing, catalysts, strategy ideas, or trade setups",
        "false_criteria": "Vague commentary, hindsight analysis, or general education"
    }
}

QUICK_QUESTIONS = {
    "relevant": {
        "type": "noul",
        "instructions": "Is this content relevant to crypto/finance research?",
    },
    "worth_reading": {
        "type": "noul",
        "instructions": "Is this worth reading in full (not just skimming)?",
        "true_criteria": "Contains novel data, actionable insights, or expert analysis",
        "false_criteria": "Generic market recap, clickbait, or shallow commentary"
    }
}


def extract_text(url: str, timeout: int = 15) -> str:
    """Fetch and extract readable text from a URL."""
    req = Request(url, headers={
        "User-Agent": "Mozilla/5.0 (compatible; HermesForge/1.0; research bot)"
    })
    try:
        with urlopen(req, timeout=timeout) as resp:
            html = resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        return f"[FETCH ERROR: {e}]"

    # Crude text extraction: strip tags
    import re
    # Remove scripts and styles
    html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
    html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL)
    # Remove tags
    text = re.sub(r'<[^>]+>', ' ', html)
    # Collapse whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    # Truncate for JEV (token budget)
    return text[:8000]


def web_search(query: str, limit: int = 5) -> list[dict]:
    """Search the web — delegates to Hermes web_search via subprocess."""
    # Use Hermes's web_search tool path if available
    import subprocess
    cmd = [
        sys.executable, "-c", f"""
import json
# Try hermes_tools path
try:
    from hermes_tools import web_search as ws
    r = ws("{query}", limit={limit})
    print(json.dumps(r))
except Exception as e:
    print(json.dumps({{"error": str(e)}}))
"""
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        data = json.loads(result.stdout)
        items = data.get("data", {}).get("web", []) if "data" in data else data.get("web", [])
        return items[:limit]
    except Exception:
        return []


def classify_content(jev: JevClient, text: str, questions: dict) -> dict:
    """Run JEV classification on content, returning structured results."""
    if not text or text.startswith("[FETCH ERROR"):
        return {"error": "No content to classify", "text_preview": text[:100]}

    results = {
        "text_length": len(text),
        "text_preview": text[:300],
        "answers": {},
        "summary": {},
    }

    for qid, qdef in questions.items():
        qtype = qdef["type"]
        instructions = qdef["instructions"]

        try:
            if qtype == "noul":
                prob = jev.noul(
                    state=text,
                    instructions=instructions,
                    true_criteria=qdef.get("true_criteria"),
                    false_criteria=qdef.get("false_criteria"),
                )
                results["answers"][qid] = {"type": "noul", "probability": round(prob, 4)}

            elif qtype == "score":
                score_result = jev.score(
                    state=text,
                    instructions=instructions,
                    levels=qdef["levels"],
                )
                results["answers"][qid] = {
                    "type": "score",
                    "score": score_result["score"],
                    "level": qdef["levels"][int(score_result["score"])] if qdef["levels"] else "N/A",
                    "confidence": round(score_result.get("confidence", 0), 4),
                }

            elif qtype == "choice":
                choice_result = jev.choice(
                    state=text,
                    instructions=instructions,
                    options=qdef["options"],
                )
                results["answers"][qid] = {
                    "type": "choice",
                    "choice": choice_result["choice"],
                    "confidence": round(choice_result.get("confidence", 0), 4),
                }
        except JevError as e:
            results["answers"][qid] = {"type": qtype, "error": str(e)[:200]}

        time.sleep(0.05)  # Light rate-limiting between questions

    # Build human-readable summary
    results["summary"] = _build_summary(results["answers"], questions)
    return results


def _build_summary(answers: dict, questions: dict) -> dict:
    """Create a concise summary from JEV answers."""
    summary = {}

    for qid, ans in answers.items():
        if "error" in ans:
            summary[qid] = f"ERROR: {ans['error'][:80]}"
            continue

        if ans["type"] == "noul":
            prob = ans["probability"]
            verdict = "YES" if prob >= 0.65 else "NO" if prob <= 0.35 else "UNCERTAIN"
            summary[qid] = f"{verdict} ({prob:.0%})"

        elif ans["type"] == "score":
            summary[qid] = f"Score: {ans['score']} — {ans['level']} (conf: {ans['confidence']:.0%})"

        elif ans["type"] == "choice":
            summary[qid] = f"{ans['choice']} (conf: {ans['confidence']:.0%})"

    return summary


def research_url(jev: JevClient, url: str, questions: dict, timeout: int = 15) -> dict:
    """Full pipeline: fetch URL → classify → return results."""
    start = time.time()
    text = extract_text(url, timeout=timeout)
    fetch_time = time.time() - start

    result = classify_content(jev, text, questions)
    result["url"] = url
    result["fetch_time_s"] = round(fetch_time, 2)
    result["total_time_s"] = round(time.time() - start, 2)
    return result


def research_search(jev: JevClient, query: str, questions: dict,
                    depth: int = 3, timeout: int = 15) -> list[dict]:
    """Search → fetch → classify pipeline for multiple results."""
    print(f"  Searching: {query}")
    results_list = web_search(query, limit=depth)

    if not results_list:
        print("  No search results found")
        return []

    for i, item in enumerate(results_list):
        url = item.get("url", "")
        title = item.get("title", "Untitled")
        print(f"  [{i+1}/{len(results_list)}] {title[:80]}...")
        result = research_url(jev, url, questions, timeout=timeout)
        result["search_rank"] = i + 1
        result["search_title"] = title
        result["search_snippet"] = item.get("description", "")
        results_list[i] = result

    return results_list


# ── CLI ──

def main():
    parser = argparse.ArgumentParser(description="JEV Browser Research Pipeline")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--url", help="Classify a single URL")
    group.add_argument("--search", help="Search query + classify top results")
    group.add_argument("--classify", help="Classify raw text (or '-' for stdin)")

    parser.add_argument("--questions", help="Path to custom questions JSON")
    parser.add_argument("--quick", action="store_true", help="Use quick 2-question mode")
    parser.add_argument("--depth", type=int, default=3, help="Search result depth (default: 3)")
    parser.add_argument("--timeout", type=int, default=15, help="Fetch timeout seconds")
    parser.add_argument("--json", action="store_true", help="Output full JSON")
    parser.add_argument("--compact", action="store_true", help="Compact output: summary only")

    args = parser.parse_args()

    # Load questions
    if args.quick:
        questions = QUICK_QUESTIONS
    elif args.questions:
        with open(args.questions) as f:
            questions = json.load(f)
    else:
        questions = DEFAULT_QUESTIONS

    # Init JEV
    try:
        jev = JevClient()
    except JevError as e:
        print(f"JEV INIT ERROR: {e}")
        sys.exit(1)

    # Run pipeline
    if args.url:
        result = research_url(jev, args.url, questions, timeout=args.timeout)
        _print_result(result, args)
    elif args.search:
        results = research_search(jev, args.search, questions, depth=args.depth, timeout=args.timeout)
        _print_results_list(results, args)
    elif args.classify:
        text = sys.stdin.read() if args.classify == "-" else args.classify
        result = classify_content(jev, text, questions)
        _print_result(result, args)


def _print_result(result: dict, args):
    if args.json:
        print(json.dumps(result, indent=2))
    elif args.compact:
        print(json.dumps(result.get("summary", {}), indent=2))
    else:
        url = result.get("url", "direct text")
        print(f"\n{'='*60}")
        print(f"JEV RESEARCH: {url}")
        print(f"{'='*60}")
        print(f"Text length: {result.get('text_length', 0)} chars")
        print(f"Fetch time: {result.get('fetch_time_s', 'N/A')}s")
        if "total_time_s" in result:
            print(f"Total time: {result['total_time_s']}s")
        print(f"\n── Classification ──")
        for qid, summary in result.get("summary", {}).items():
            print(f"  {qid:20s}: {summary}")
        print()


def _print_results_list(results: list, args):
    print(f"\n{'='*60}")
    print(f"JEV RESEARCH: {len(results)} results")
    print(f"{'='*60}\n")

    for i, r in enumerate(results):
        rank = r.get("search_rank", i+1)
        title = r.get("search_title", r.get("url", "unknown"))
        url = r.get("url", "")
        print(f"[{rank}] {title[:100]}")
        print(f"    {url[:100]}")
        for qid, summary in r.get("summary", {}).items():
            print(f"    {qid:20s}: {summary}")
        print()


if __name__ == "__main__":
    main()