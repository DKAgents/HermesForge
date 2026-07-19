"""
model_review.py — Biweekly Model Assignment Review (HermesForge)

Reviews actual model usage/cost against the ADR-001 tier assignments and
flags opportunities to downgrade (save cost, no quality loss) or upgrade
(quality issues observed, worth paying more).

Data sources:
  - hermes insights (session/token stats per model)
  - Headroom proxy stats (cost with/without optimization)
  - Cron job model assignments (~/.hermes/cron/jobs.json)
  - OpenRouter model catalog (for current pricing)

This script does NOT change any config — it only reports. Model changes
require explicit human approval per SOUL.md risk rules.
"""

import json
import subprocess
import pathlib
import datetime
from urllib.request import urlopen, Request

HOME = pathlib.Path.home()
CRON_JOBS_FILE = HOME / ".hermes" / "cron" / "jobs.json"
ADR_PATH = pathlib.Path.home() / "HermesForge" / "03-ADRs" / "ADR-001-Model-Routing-Strategy.md"

# Tier reference from ADR-001 (2026-07-20) — kept in sync manually
TIER_MODELS = {
    "T1": "anthropic/claude-opus-4.8",
    "T2": "anthropic/claude-sonnet-5",
    "T3": "deepseek/deepseek-v4-flash",
    "T4": "google/gemini-2.0-flash-001",
}

HARD_FLOOR_PROFILES = {"risk-guardian", "orchestrator", "architect", "coder"}


def run(cmd: str) -> str:
    return subprocess.run(cmd, shell=True, capture_output=True, text=True).stdout


def get_insights(days: int = 14) -> str:
    return run(f"hermes insights --days {days}")


def get_cron_models() -> list[dict]:
    if not CRON_JOBS_FILE.exists():
        return []
    data = json.loads(CRON_JOBS_FILE.read_text())
    jobs = data.get("jobs", [])
    return [
        {"id": j.get("id", "")[:12], "name": j.get("name", ""), "model": j.get("model") or "(default)"}
        for j in jobs
    ]


def get_openrouter_pricing(model_ids: list[str]) -> dict:
    """Fetch current pricing for given model IDs from OpenRouter's public model list."""
    try:
        req = Request("https://openrouter.ai/api/v1/models", headers={"User-Agent": "HermesForge-Review"})
        with urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
        pricing = {}
        for m in data.get("data", []):
            mid = m.get("id", "")
            if mid in model_ids:
                p = m.get("pricing", {})
                pricing[mid] = {
                    "prompt": float(p.get("prompt", 0)) * 1_000_000,
                    "completion": float(p.get("completion", 0)) * 1_000_000,
                }
        return pricing
    except Exception as e:
        return {"_error": str(e)}


def get_headroom_stats() -> dict:
    try:
        raw = run("curl -s --max-time 5 http://127.0.0.1:8787/stats")
        return json.loads(raw)
    except Exception as e:
        return {"_error": str(e)}


def build_report() -> str:
    today = datetime.date.today().isoformat()
    insights = get_insights(14)
    cron_models = get_cron_models()
    headroom = get_headroom_stats()

    tier_pricing = get_openrouter_pricing(list(TIER_MODELS.values()))

    lines = [
        f"# Biweekly Model Assignment Review — {today}",
        "",
        "## Current Tier Assignments (ADR-001)",
        "",
        "| Tier | Model | Current Price (in/out per 1M) |",
        "|---|---|---|",
    ]
    for tier, model in TIER_MODELS.items():
        p = tier_pricing.get(model, {})
        if p and "prompt" in p:
            price_str = f"${p['prompt']:.2f} / ${p['completion']:.2f}"
        else:
            price_str = "(pricing unavailable)"
        lines.append(f"| {tier} | `{model}` | {price_str} |")

    lines += [
        "",
        "## Cron Job Model Assignments (Actual)",
        "",
        "| Job | Model |",
        "|---|---|",
    ]
    for j in cron_models:
        lines.append(f"| {j['name']} | `{j['model']}` |")

    lines += [
        "",
        "## Usage & Cost (Last 14 Days)",
        "",
        "```",
        insights.strip(),
        "```",
        "",
        "## Headroom Proxy Savings",
        "",
    ]
    if "_error" in headroom:
        lines.append(f"⚠️ Headroom stats unavailable: {headroom['_error']}")
    else:
        summary = headroom.get("summary", {})
        cost = summary.get("cost", {})
        lines.append(f"- Total saved: ${cost.get('total_saved_usd', 0):.2f} ({cost.get('savings_pct', 0):.1f}%)")
        lines.append(f"- Requests: {summary.get('api_requests', 0)}")

    lines += [
        "",
        "## Review Questions (answer manually or via delegated analysis)",
        "",
        "1. **Any hard-floor profile (risk-guardian, orchestrator, architect, coder) showing",
        "   quality complaints, errors, or task failures at T2?** If none — no change needed.",
        "   If yes — do NOT downgrade; consider T1 escalation instead.",
        "2. **Any T3/T4 automation cron showing errors, poor output quality, or requiring",
        "   frequent manual correction?** If yes — consider escalating that specific job to T2.",
        "   If no issues — T3/T4 assignment is validated, no change needed.",
        "3. **Has any tier's pricing changed materially since last review?**",
        "   (Check the pricing table above against the prior report.)",
        "4. **Sonnet 5 introductory pricing status** — expires Aug 31, 2026.",
        "   Days remaining: " + str((datetime.date(2026, 8, 31) - datetime.date.today()).days),
        "",
        "## Recommendation",
        "",
        "_(Fill in after reviewing the above — no cost savings should come at the expense",
        "of hard-floor profile quality. Any proposed downgrade requires explicit approval",
        "before implementation, per SOUL.md risk rules.)_",
        "",
    ]

    return "\n".join(lines)


if __name__ == "__main__":
    report = build_report()
    print(report)
