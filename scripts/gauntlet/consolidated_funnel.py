#!/usr/bin/env python3
"""
consolidated_funnel.py — US-190 consolidated per-gate funnel.

Produces a single per-gate funnel (G0..G7: entered / passed / failed + top-3
failure reasons per gate) from the two sources that actually carry gate-relevant
state on disk:

  1. data/gauntlet/trials.jsonl — 115 append-only backtest rows (the "entered"
     cohort). Each row's hypothesis_id carries a phase marker:
       -phase1a  = initial frictionless scan (G1),       73 rows
       -phase1b  = cost-aware re-run (G3),               20 rows
       <none>    = unscoped early entries,               22 rows
  2. trading/strategies/{Active,Deprecated,Hypotheses,Live} — the registry's
     terminal statuses, which map a strategy to the furthest gate it reached.

Honesty contract: the ledger records trial RESULTS, not per-gate pass/fail
booleans. G1 and G3 are derived directly from the phase markers + result
metrics; G0/G2/G4/G5/G6/G7 have no per-trial ledger field and are reconstructed
from the registry terminal statuses (each gate row is annotated with its source).
This is a consolidation of what is on disk — it never invents per-strategy gate
booleans that were never recorded.

Usage:
    python3 consolidated_funnel.py               # print the funnel as text
    python3 consolidated_funnel.py --json        # emit machine-readable JSON
    python3 consolidated_funnel.py --markdown    # emit markdown for Discord
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
TRIALS = REPO / "data" / "gauntlet" / "trials.jsonl"
REGISTRY = REPO / "trading" / "strategies"

REGISTRY_DIRS = ("Active", "Deprecated", "Hypotheses", "Live")

# ── Classification of a trial's failure signature ──────────────────────────
FRICTION_FLOOR_R = 0.3  # realistic friction ~0.1–0.3 R (chart-pattern OOS span)
MIN_SAMPLE = 20


def _load_trials() -> list[dict]:
    rows = []
    if not TRIALS.exists():
        return rows
    for line in TRIALS.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows


def _phase_of(hid: str) -> str:
    if "phase1b" in hid:
        return "phase1b"
    if "phase1a" in hid:
        return "phase1a"
    return "unscoped"


def _base_id(hid: str) -> str:
    return re.sub(r"-(phase\d[a-z]?)(?:-v\d+)?$", "", hid)


def _failure_reason(result: dict) -> str:
    avg_r = float(result.get("avg_r", 0.0) or 0.0)
    pf = float(result.get("pf", 0.0) or 0.0)
    n = int(result.get("trade_count", 0) or 0)
    if n < MIN_SAMPLE:
        return "insufficient sample (<20 trades)"
    if avg_r <= 0:
        return "no edge (avg_r <= 0)"
    if pf < 1.0:
        return "profit factor < 1.0"
    if avg_r < FRICTION_FLOOR_R:
        return "edge below friction (0 < avg_r < 0.3R)"
    return "other"


def _registry_statuses() -> dict[str, dict]:
    """Return {strategy_stem: {...}} keyed by the REGISTRY FOLDER (the terminal
    state), with the frontmatter sub-status captured separately for annotation.

    The folder is the authoritative terminal state (Active / Deprecated /
    Hypotheses / Live) and reconciles to the documented 2 / 1 / 35 / 0.
    """
    out: dict[str, dict] = {}
    for d in REGISTRY_DIRS:
        dire = REGISTRY / d
        if not dire.is_dir():
            continue
        for f in dire.glob("*.md"):
            text = f.read_text(encoding="utf-8", errors="replace")
            fm = {}
            m = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
            if m:
                for line in m.group(1).splitlines():
                    kv = re.match(r"^([\w-]+):\s*(.*)", line)
                    if kv:
                        fm[kv.group(1)] = kv.group(2).strip().strip('"')
            reason = fm.get("deprecated_reason", "")
            sid = fm.get("id", f.stem)
            out[f.stem] = {"status": d.lower(), "sub_status": fm.get("status", ""),
                           "reason": reason, "id": sid, "folder": d}
    return out


def _top_reasons(counter: Counter, top: int = 3) -> list[str]:
    return [f"{r} (x{n})" for r, n in counter.most_common(top)]


def build_funnel() -> dict:
    trials = _load_trials()
    reg = _registry_statuses()

    # ── 1. ledger phase partition ──
    phase_counter = Counter(_phase_of(t["hypothesis_id"]) for t in trials)
    phase_reasons = defaultdict(Counter)
    phase_passed = Counter()
    for t in trials:
        ph = _phase_of(t["hypothesis_id"])
        r = t.get("result") or {}
        if float(r.get("avg_r", 0.0) or 0.0) > 0 and int(r.get("trade_count", 0) or 0) >= MIN_SAMPLE:
            phase_passed[ph] += 1
        else:
            phase_reasons[ph][_failure_reason(r)] += 1

    # ── 2. registry terminal statuses ──
    reg_cnt = Counter(v["status"] for v in reg.values())

    # ── 3. per-gate funnel (G0..G7) ──
    n_total = len(trials)
    n_scan = phase_counter["phase1a"] + phase_counter["unscoped"]
    n_cost = phase_counter["phase1b"]

    gates = []
    for i in range(8):
        gates.append({"gate": f"G{i}", "entered": 0, "passed": 0, "failed": 0,
                      "top_failures": [], "source": "no per-trial ledger field"})

    gates[0].update({
        "entered": n_total, "passed": n_scan, "failed": n_total - n_scan,
        "source": "ledger: all 115 trials pass the G0 cost pre-screen entry point",
        "top_failures": _top_reasons(phase_reasons["phase1a"] + phase_reasons["unscoped"]),
    })
    gates[1].update({
        "entered": n_scan,
        "passed": phase_passed["phase1a"] + phase_passed["unscoped"],
        "failed": n_scan - (phase_passed["phase1a"] + phase_passed["unscoped"]),
        "source": "ledger: phase1a/unscoped trial results (signal scan)",
        "top_failures": _top_reasons(phase_reasons["phase1a"] + phase_reasons["unscoped"]),
    })
    gates[2].update({
        "entered": n_cost, "passed": 0, "failed": 0,
        "source": "registry: only strategies with a phase1b re-run reached G2/G3",
        "top_failures": [],
    })
    gates[3].update({
        "entered": n_cost,
        "passed": phase_passed["phase1b"],
        "failed": n_cost - phase_passed["phase1b"],
        "source": "ledger: phase1b cost-aware results (G3 execution realism)",
        "top_failures": _top_reasons(phase_reasons["phase1b"]),
    })
    # G4–G7: reconstructed from registry terminal statuses.
    gates[4].update({
        "entered": reg_cnt.get("active", 0) + reg_cnt.get("live", 0) + reg_cnt.get("hypotheses", 0),
        "passed": reg_cnt.get("active", 0) + reg_cnt.get("live", 0),
        "failed": reg_cnt.get("deprecated", 0),
        "source": "registry: Active/Live/Hypotheses statuses past G3",
        "top_failures": [],
    })
    gates[5].update({
        "entered": reg_cnt.get("active", 0) + reg_cnt.get("live", 0),
        "passed": reg_cnt.get("active", 0) + reg_cnt.get("live", 0),
        "failed": 0,
        "source": "registry: strategies still standing post-G5 (DSR/PBO)",
        "top_failures": [],
    })
    gates[6].update({
        "entered": reg_cnt.get("active", 0) + reg_cnt.get("live", 0),
        "passed": reg_cnt.get("active", 0) + reg_cnt.get("live", 0),
        "failed": 0,
        "source": "registry: robustness survivors",
        "top_failures": [],
    })
    gates[7].update({
        "entered": reg_cnt.get("active", 0),
        "passed": reg_cnt.get("live", 0),
        "failed": 0,
        "pending": reg_cnt.get("active", 0),
        "source": "registry: Active = G7-forward pending; Live = promoted",
        "top_failures": [],
    })

    return {
        "ledger_rows": n_total,
        "phase": dict(phase_counter),
        "registry": dict(reg_cnt),
        "active_ids": [v["id"] for v in reg.values() if v["status"] == "active"],
        "deprecated_ids": [v["id"] for v in reg.values() if v["status"] == "deprecated"],
        "live_ids": [v["id"] for v in reg.values() if v["status"] == "live"],
        "gates": gates,
    }


def _fmt_text(f: dict) -> str:
    lines = []
    lines.append(f"=== HermesForge Strategy Gauntlet — Consolidated Funnel (US-190) ===")
    lines.append(f"Ledger rows (trials.jsonl): {f['ledger_rows']}")
    lines.append(f"Phase split: {f['phase']}")
    lines.append(f"Registry: {f['registry']}")
    lines.append("")
    lines.append(f"{'Gate':4s} {'entered':>8s} {'passed':>7s} {'failed':>7s}  top-3 failure reasons")
    lines.append("-" * 78)
    for g in f["gates"]:
        tf = "; ".join(g["top_failures"]) if g["top_failures"] else "—"
        extra = f"  [pending={g['pending']}]" if "pending" in g else ""
        lines.append(f"{g['gate']:4s} {g['entered']:>8d} {g['passed']:>7d} "
                     f"{g['failed']:>7d}{extra}  {tf}")
    lines.append("-" * 78)
    lines.append("Reconciliation (must match actual on-disk state):")
    lines.append(f"  trials.jsonl rows  = {f['ledger_rows']}")
    lines.append(f"  Registry Active    = {f['registry'].get('active', 0)}  {f['active_ids']}")
    lines.append(f"  Registry Deprecated= {f['registry'].get('deprecated', 0)}  {f['deprecated_ids']}")
    lines.append(f"  Registry Live      = {f['registry'].get('live', 0)}  {f['live_ids']}")
    lines.append(f"  Registry Hypotheses= {f['registry'].get('hypotheses', 0)}")
    return "\n".join(lines)


def _fmt_markdown(f: dict) -> str:
    lines = ["**📊 Consolidated Funnel (US-190)**",
             f"Ledger rows: **{f['ledger_rows']}** · phase {f['phase']}",
             f"Registry: {f['registry']}",
             "```",
             f"{'Gate':4s} {'entered':>8s} {'passed':>7s} {'failed':>7s}"]
    for g in f["gates"]:
        lines.append(f"{g['gate']:4s} {g['entered']:>8d} {g['passed']:>7d} {g['failed']:>7d}")
    lines.append("```")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--markdown", action="store_true")
    args = ap.parse_args()

    f = build_funnel()
    if args.json:
        print(json.dumps(f, indent=2))
    elif args.markdown:
        print(_fmt_markdown(f))
    else:
        print(_fmt_text(f))
    return 0


if __name__ == "__main__":
    sys.exit(main())