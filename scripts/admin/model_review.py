"""
model_review.py — Biweekly Model Assignment Review (HermesForge)

Reviews actual model usage/cost against the ADR-001 tier assignments and
flags opportunities to downgrade (save cost, no quality loss) or upgrade
(quality issues observed, worth paying more).

Data sources:
  - hermes insights (session/token stats per model, direct from OpenRouter)
  - Cron job model assignments (~/.hermes/cron/jobs.json)
  - OpenRouter model catalog (for current pricing)

NOTE: Headroom proxy was intentionally disabled 2026-07-27 when the fleet
      switched to direct OpenRouter access. All cost/usage data now comes
      from `hermes insights` (which queries OpenRouter's usage endpoint).

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
ADR_PATH = HOME / "HermesForge" / "03-ADRs" / "ADR-001-Model-Routing-Strategy.md"

# Tier reference — synced from ADR-001 (last updated 2026-08-25)
TIER_MODELS = {
    "T1": "anthropic/claude-opus-4.8",
    "T2": "deepseek/deepseek-v4-pro",
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
    results = []
    for j in jobs:
        model = j.get("model", "")
        provider = j.get("provider", "")
        no_agent = j.get("no_agent", False)
        if no_agent:
            model_str = "no-agent (script only)"
        elif provider and model:
            model_str = f"{provider}/{model}"
        elif model:
            model_str = model
        else:
            model_str = "(default)"
        results.append({
            "id": j.get("id", "")[:12],
            "name": j.get("name", ""),
            "model": model_str,
            "explicit_tier": bool(model) or no_agent,
        })
    return results


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


def parse_insights_tokens(insights_text: str) -> dict:
    """Parse 'hermes insights' output to extract per-model token counts and cost.

    Returns: dict with model-level {model: {sessions, tokens_in, tokens_out, cost}}.
    """
    models = {}
    in_table = False
    models_done = False
    for line in insights_text.split("\n"):
        stripped = line.strip()

        # Only enter the FIRST table (Models, not Platforms)
        if not models_done and "Model" in stripped and "Sessions" in stripped and "Tokens" in stripped:
            in_table = True
            continue

        # "Platform" table header => stop parsing. We only want model-level data.
        if in_table and ("Platform" in stripped):
            in_table = False
            models_done = True
            continue

        # Separator line ends the Models table
        if in_table and (stripped.startswith("---") or stripped.startswith("===") or not stripped):
            in_table = False
            models_done = True
            continue

        if in_table and stripped:
            parts = stripped.split()
            if len(parts) >= 3:
                # Name may be multi-word; data is in the last 3 columns: Sessions, Tokens, Cost
                try:
                    sessions = int(parts[-3].replace(",", ""))
                    tokens = int(parts[-2].replace(",", ""))
                    cost_val = float(parts[-1].replace("$", "").replace(",", "")) if parts[-1].replace(",", "").replace(".", "").replace("-", "").isdigit() else 0
                except (ValueError, IndexError):
                    continue
                name = " ".join(parts[:-3])
                models[name.strip()] = {
                    "sessions": sessions,
                    "tokens": tokens,
                    "cost": cost_val,
                }
    return models


def build_report() -> str:
    today = datetime.date.today().isoformat()
    insights = get_insights(14)
    cron_models = get_cron_models()
    tier_pricing = get_openrouter_pricing(list(TIER_MODELS.values()))
    model_usage = parse_insights_tokens(insights)

    lines = [
        f"# 📊 Biweekly Model Assignment Review — {today}",
        "",
        "## 1. Tier Assignments & Current Pricing",
        "",
        "| Tier | Model | Price (in/out per 1M) |",
        "|---|---|---|",
    ]
    for tier, model in TIER_MODELS.items():
        p = tier_pricing.get(model, {})
        if p and "prompt" in p:
            price_str = f"${p['prompt']:.2f} / ${p['completion']:.2f}"
        else:
            price_str = "_(pricing unavailable)_"
        lines.append(f"| **{tier}** | `{model}` | {price_str} |")

    lines += [
        "",
        "## 2. Cron Job Model Assignments",
        "",
        "| Job Name | Model | Explicit? |",
        "|---|---|---|",
    ]
    unassigned_count = 0
    for j in cron_models:
        explicit = "✅" if j["explicit_tier"] else "⚠️"
        if not j["explicit_tier"]:
            unassigned_count += 1
        lines.append(f"| {j['name']} | `{j['model']}` | {explicit} |")

    compliance = "✅ 100% compliance" if unassigned_count == 0 else f"⚠️ {unassigned_count} unassigned"
    lines += [
        "",
        f"**ADR-001 compliance:** {compliance}",
        "",
        "## 3. Cost Analysis (Last 14 Days)",
        "",
    ]

    if model_usage:
        lines.append("| Model | Sessions | Tokens | Est. Cost |")
        lines.append("|---|---|---|---|")
        total_cost = 0.0
        for name, stats in sorted(model_usage.items(), key=lambda x: x[1].get("tokens", 0), reverse=True):
            cost = stats.get("cost", 0)
            total_cost += cost
            lines.append(f"| {name} | {stats['sessions']:,} | {stats['tokens']:,} | ~${cost:.2f} |")
        lines += [
            "",
            f"**Estimated 14-day spend:** ~${total_cost:.2f}",
            f"**Estimated monthly:** ~${total_cost * 2.17:.2f}",
        ]

    lines += [
        "",
        "```",
        insights.strip() if insights.strip() else "(hermes insights returned no data)",
        "```",
        "",
        "## 4. Quality Check — Hard-Floor Profiles",
        "",
        "Hard-floor profiles (risk-guardian, orchestrator, architect, coder): T2 minimum per ADR-001.",
        "The fleet uses `deepseek-v4-pro` as T2 (switched from GLM-5.2 on 2026-08-23).",
        "All T3 cron jobs use `deepseek-v4-flash` (migrated 2026-08-24).",
        "",
        "**Note:** Headroom proxy has been intentionally disabled (2026-07-27).",
        "The fleet connects to OpenRouter directly. All cost/usage data comes from",
        "`hermes insights`, which queries OpenRouter's authenticated usage endpoint.",
        "No quality/error-rate proxy is available — spot-check critical cron outputs",
        "manually for regressions.",
        "",
        "## 5. Review Questions",
        "",
        "1. **Any hard-floor profile (risk-guardian, orchestrator, architect, coder) showing",
        "   quality complaints, errors, or task failures at T2?** If none — no change needed.",
        "   If yes — do NOT downgrade; consider T1 escalation instead.",
        "2. **Any T3/T4 automation cron showing errors, poor output quality, or requiring",
        "   frequent manual correction?** If yes — consider escalating that specific job to T2.",
        "   If no issues — T3/T4 assignment is validated, no change needed.",
        "3. **Has any tier's pricing changed materially since last review?**",
        "   (Check the pricing table above against the prior report.)",
        "4. **T1 escalation log review** — check `08-Knowledge/T1-Escalations/` for recent",
        "   escalations. Did Opus change the outcome vs what T2 would have produced?",
        "   If T1 never fires, triggers may need adjusting (see ADR-001 Section 2b).",
        "",
        "## 6. Recommendation",
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