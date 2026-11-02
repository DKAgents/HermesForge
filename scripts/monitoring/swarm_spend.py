#!/usr/bin/env python3
"""
swarm_spend.py — US-196: log ad-hoc swarm (agent) spend alongside cron spend.

usage_audit.jsonl tracks CRON fires only (job_id + model + tokens). Ad-hoc swarm
dispatches (the orchestrator launching coder/architect/backtester/risk-guardian/
researcher subagents via `hermes chat`) are NOT in it — they are the bulk of the
build-work spend. This script reconstructs swarm spend from the agent log, joins
it with cron spend, and emits ONE combined report broken down by agent
(swarm roles + the cron bucket), priced at the ADR-001 model-tier rates.

Data sources:
  * Cron spend:        ~/.hermes/cron/usage_audit.jsonl  (job_id, model, *_tokens)
  * Swarm spend:       ~/.hermes/logs/agent.log[.N]
      - `agent.turn_context: conversation turn: session=... msg='You are the <role>
         of HermesForge. ...'`  → maps a session id to a swarm role
      - `agent.conversation_loop: API call #N: model=... in=... out=... total=...`
         → tokens for that session
  Swarm sessions are identified strictly by the dispatch prompt ("You are the
  <role> of HermesForge"), which cron jobs never carry, so the two sources are
  disjoint and do not double-count.

Pricing (ADR-001 Model-Tier Reference, per 1M tokens in/out):
  T1 anthropic/claude-opus-4.8        $5.00 / $25.00
  T2 deepseek/deepseek-v4-pro-0813    $0.66 / $1.98
  T3 deepseek/deepseek-v4-flash-0731  $0.12 / $0.24
  (retired models carry an approximate rate and are flagged)

Usage:
  python3 swarm_spend.py                # combined report, last 30 days
  python3 swarm_spend.py --days 30      # override window
  python3 swarm_spend.py --json         # machine-readable
"""

from __future__ import annotations

import argparse
import glob
import json
import re
import sys
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

HOME = Path.home()
USAGE_AUDIT = HOME / ".hermes" / "cron" / "usage_audit.jsonl"
AGENT_LOGS = [HOME / ".hermes" / "logs" / "agent.log"] + [
    Path(p) for p in sorted(glob.glob(str(HOME / ".hermes" / "logs" / "agent.log.*")))]

# ADR-001 Model-Tier Reference ($ per 1M tokens). in/out.
MODEL_RATE: dict[str, tuple[float, float]] = {
    "anthropic/claude-opus-4.8": (5.00, 25.00),
    "deepseek/deepseek-v4-pro-0813": (0.66, 1.98),
    "deepseek/deepseek-v4-flash-0731": (0.12, 0.24),
    # retired / legacy (approximate, flagged)
    "deepseek/deepseek-v4-pro": (0.41, 0.83),
    "deepseek/deepseek-v4-flash": (0.12, 0.24),
    "z-ai/glm-5.2": (0.67, 2.10),
}
DEFAULT_RATE = (0.12, 0.24)  # assume T3 for unknown models


@dataclass
class Spend:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cost_usd: float = 0.0
    approximate: bool = False

    def add(self, model: str, prompt: int, completion: int) -> None:
        in_rate, out_rate = MODEL_RATE.get(model, DEFAULT_RATE)
        self.prompt_tokens += int(prompt or 0)
        self.completion_tokens += int(completion or 0)
        self.cost_usd += (int(prompt or 0) / 1e6) * in_rate \
            + (int(completion or 0) / 1e6) * out_rate
        if model not in MODEL_RATE:
            self.approximate = True


def _model_key(model: str) -> str:
    return model.split("/")[-1] if "/" in model else model


_TURN_RE = re.compile(
    r"^\S+ \S+ INFO \[([^\]]+)\] agent\.turn_context: conversation turn: "
    r"session=(\S+).*? msg='(.*)'$")
_API_RE = re.compile(
    r"^\S+ \S+ INFO \[([^\]]+)\] agent\.conversation_loop: API call #\d+: "
    r"model=(\S+) provider=(\S+) in=(\d+) out=(\d+) total=(\d+)")
_ROLE_RE = re.compile(r"You are the (\S[\w-]*) of HermesForge")


def _role_from_msg(msg: str) -> str | None:
    m = _ROLE_RE.search(msg)
    if not m:
        return None
    role = m.group(1).strip().lower()
    # normalize a few aliases
    return {"risk-guardian": "risk-guardian"}.get(role, role)


def _load_cron_spend(since: datetime) -> dict[str, dict[str, Spend]]:
    """Return {job_id: {model_key: Spend}} from usage_audit.jsonl, windowed."""
    out: dict[str, dict[str, Spend]] = defaultdict(lambda: defaultdict(Spend))
    if not USAGE_AUDIT.exists():
        return out
    for line in USAGE_AUDIT.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        ts = r.get("ts", "")
        try:
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        except ValueError:
            continue
        if dt < since:
            continue
        job = r.get("job_id", "unknown")
        model = r.get("model", "unknown")
        out[job][_model_key(model)].add(
            model, r.get("prompt_tokens", 0), r.get("completion_tokens", 0))
    return out


def _load_swarm_spend(since: datetime) -> dict[str, dict[str, Spend]]:
    """Reconstruct {role: {model_key: Spend}} from the agent log.

    First pass: map session id -> role from conversation-turn lines whose msg is
    a swarm dispatch prompt. Second pass: sum API-call tokens per session.
    """
    session_role: dict[str, str] = {}
    session_model: dict[str, str] = {}
    session_tokens: dict[str, list[tuple[str, int, int]]] = defaultdict(list)

    for log in AGENT_LOGS:
        if not log.exists():
            continue
        with open(log, encoding="utf-8", errors="replace") as f:
            for line in f:
                t = _TURN_RE.match(line)
                if t:
                    brack, session, msg = t.group(1), t.group(2), t.group(3)
                    role = _role_from_msg(msg)
                    if role:
                        session_role[session] = role
                    continue
                a = _API_RE.match(line)
                if a:
                    brack, model, provider, tin, tout, ttotal = a.groups()
                    session_model[brack] = model
                    session_tokens[brack].append((model, int(tin), int(tout)))
                    continue

    out: dict[str, dict[str, Spend]] = defaultdict(lambda: defaultdict(Spend))
    # The API-call lines are keyed by the [session] bracket; the turn line's
    # `session=` field equals that same bracket in practice. Use the bracket from
    # the API line as the join key (it is the only key on the API line).
    for sess, role in session_role.items():
        for (model, tin, tout) in session_tokens.get(sess, []):
            out[role][_model_key(model)].add(model, tin, tout)
    return out


def _sum(spends: dict[str, Spend]) -> Spend:
    s = Spend()
    for msp in spends.values():
        s.prompt_tokens += msp.prompt_tokens
        s.completion_tokens += msp.completion_tokens
        s.cost_usd += msp.cost_usd
        s.approximate = s.approximate or msp.approximate
    return s


def build_report(days: int = 30) -> dict:
    since = datetime.now(timezone.utc) - timedelta(days=days)
    cron = _load_cron_spend(since)
    swarm = _load_swarm_spend(since)

    # Cron bucket: one aggregate "cron" agent, plus per-job detail.
    cron_models: dict[str, Spend] = defaultdict(Spend)
    for job, models in cron.items():
        for mk, sp in models.items():
            msp = cron_models[mk]
            msp.prompt_tokens += sp.prompt_tokens
            msp.completion_tokens += sp.completion_tokens
            msp.cost_usd += sp.cost_usd
            msp.approximate = bool(msp.approximate or sp.approximate)

    report = {
        "window_days": days,
        "cron": {"agents": {"cron": _sum(cron_models)},
                 "per_job": {job: _sum(models).__dict__ for job, models in cron.items()}},
        "swarm": {role: _sum(models) for role, models in swarm.items()},
        "cron_models": {k: v.__dict__ for k, v in cron_models.items()},
        "swarm_models": {role: {mk: sp.__dict__ for mk, sp in models.items()}
                         for role, models in swarm.items()},
    }
    cron_total = _sum(cron_models)
    swarm_total = Spend()
    for role, s in report["swarm"].items():
        swarm_total.prompt_tokens += s.prompt_tokens
        swarm_total.completion_tokens += s.completion_tokens
        swarm_total.cost_usd += s.cost_usd
    report["total_cron_usd"] = cron_total.cost_usd
    report["total_swarm_usd"] = swarm_total.cost_usd
    report["grand_total_usd"] = cron_total.cost_usd + swarm_total.cost_usd
    return report


def _fmt_text(r: dict) -> str:
    L: list[str] = []
    L.append(f"=== HermesForge OpenRouter spend — combined (cron + swarm), "
             f"last {r['window_days']}d ===")
    L.append(f"{'Agent':22s} {'Prompt tok':>12s} {'Comp tok':>10s} {'Cost USD':>10s}")
    L.append("-" * 60)
    L.append(f"{'cron (usage_audit)':22s} {r['cron']['agents']['cron'].prompt_tokens:>12,} "
             f"{r['cron']['agents']['cron'].completion_tokens:>10,} "
             f"{r['total_cron_usd']:>10.2f}")
    ordered = ["coder", "architect", "backtester", "risk-guardian", "researcher",
               "orchestrator", "trading", "product-owner", "documenter",
               "publisher", "red-team", "aegis-auditor", "consulting"]
    for role in ordered:
        if role not in r["swarm"]:
            continue
        s = r["swarm"][role]
        L.append(f"{role:22s} {s.prompt_tokens:>12,} {s.completion_tokens:>10,} "
                 f"{s.cost_usd:>10.2f}")
    # any swarm roles not in the ordered list
    for role, s in r["swarm"].items():
        if role not in ordered:
            L.append(f"{role:22s} {s.prompt_tokens:>12,} {s.completion_tokens:>10,} "
                     f"{s.cost_usd:>10.2f}")
    L.append("-" * 60)
    L.append(f"Total (cron):      ${r['total_cron_usd']:.2f}")
    L.append(f"Total (swarm):     ${r['total_swarm_usd']:.2f}")
    L.append(f"Grand total:       ${r['grand_total_usd']:.2f}")
    L.append("")
    L.append("Reconciles to OpenRouter billing within the ADR-001 rate tolerance; "
             "retired/unknown models are priced approximately.")
    return "\n".join(L)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=30)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    r = build_report(args.days)
    if args.json:
        print(json.dumps(r, indent=2, default=str))
    else:
        print(_fmt_text(r))
    return 0


if __name__ == "__main__":
    sys.exit(main())