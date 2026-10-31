#!/usr/bin/env python3
"""system_doctor/collector.py — US-158 Phase-1 detection-only collector.

A read-only, STDLIB-ONLY scan of live HermesForge state that emits a shared
findings queue (JSONL) consumed later by the Orchestrator (US-159, out of
scope). No auto-fix. No third-party imports — this doctor must keep running
even when the very dependency rot it detects (yaml/requests/mplfinance/...)
is present elsewhere.

Binds to SPEC-US-158-161-Phase1-system-doctor.md (design-approved 2026-10-31).

Read-only guarantees (Section 5.1): the ONLY side-effecting syscalls are
the queue write and the state-file write, both via temp-file + os.replace
(atomic-write convention). Every probe is read-only (stat/head/git status/
df/systemctl is-active/sshd -T/GET). No pip, no git pull/push, no file
mutation outside cache/system-doctor/, no secret access, no service restart.

Stdlib surface: json, pathlib, hashlib, subprocess, urllib, shutil, os,
sys, datetime, re, collections.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.request import Request, urlopen

# --------------------------------------------------------------------------
# Paths — production defaults, overridable via environment for testability.
# --------------------------------------------------------------------------
HF_ROOT = Path(os.environ.get("HERMESFORGE_ROOT", "/root/HermesForge"))
CACHE_DIR = Path(os.environ.get("SYSTEM_DOCTOR_CACHE", f"{HF_ROOT}/cache/system-doctor"))


def _findings_jsonl() -> Path:
    """Queue path, re-resolved from env at call time (test isolation)."""
    return Path(os.environ.get("SYSTEM_DOCTOR_CACHE", str(CACHE_DIR))) / "findings.jsonl"


def _state_json() -> Path:
    return Path(os.environ.get("SYSTEM_DOCTOR_CACHE", str(CACHE_DIR))) / "findings.state.json"


# Backwards-compatible aliases for callers that expect the module constant.
FINDINGS_JSONL = _findings_jsonl()
STATE_JSON = _state_json()

CRON_DIR = Path(os.environ.get("SYSTEM_DOCTOR_CRON_DIR", "/root/.hermes/cron"))
JOBS_JSON = CRON_DIR / "jobs.json"
CRON_OUTPUT = CRON_DIR / "output"
USAGE_AUDIT = CRON_DIR / "usage_audit.jsonl"

# OpenRouter model list endpoints (read-only GET).
OR_ENDPOINTS = (
    "http://127.0.0.1:8787/v1/models",      # Headroom proxy
    "https://openrouter.ai/api/v1/models",  # public API
)

# --------------------------------------------------------------------------
# Thresholds & constants (resolved decisions D4/D6 + Section 1 tables).
# --------------------------------------------------------------------------
STALE_WINDOW = timedelta(hours=24)          # dedup suppression window
RETENTION_DAYS = 90                          # D4 (Phase 2 archive; noted only)
COST_CAP_USD = 8.0                           # D6 soft ceiling, trailing 30d
COST_TRAILING_DAYS = 30
DISK_WARN_PCT = 85
DISK_CRIT_PCT = 92
GIT_DIRTY_AGE = timedelta(hours=24)          # "persisting >24h" issue threshold
GIT_COMMIT_CADENCE = timedelta(days=14)      # optimization ("stale commit")

# Per-model pricing ($ per 1M input / output tokens) for cost estimate.
# Source: ADR-001 tier table + runtime facts.json. Models not listed are
# treated as "unpriced" and surfaced as a pricing-gap note (fail-closed).
MODEL_PRICE = {
    "deepseek/deepseek-v4-pro": (0.41, 0.83),
    "deepseek/deepseek-v4-flash": (0.05, 0.11),
    "deepseek/deepseek-v4-flash-0731": (0.05, 0.11),
}

CATEGORIES = [
    "cron_error",
    "data_freshness",
    "model_staleness",
    "cost_drift",
    "disk_ssh_security",
    "upstream_git",
]

VERDICTS = {"clean", "finding", "not_inspected", "error"}

_DEP_RE = re.compile(
    r"(ModuleNotFoundError|No module named|ImportError|missing module|"
    r"pip install|not found in|no dependencies|ruamel|truststore)", re.I)


def _squash(s: str, limit: int = 300) -> str:
    """Collapse whitespace so evidence strings embed on one digest line."""
    s = re.sub(r"\s+", " ", (s or "").strip())
    return s[:limit]


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def normalize(text: str) -> str:
    """Dedup normalize: lowercase + strip timestamps/ids/numbers (2.4.1)."""
    text = re.sub(r"\d+", "", text)
    text = re.sub(r"[^\w\s]", " ", text.lower())
    return re.sub(r"\s+", " ", text).strip()


def dedup_key(category: str, source: str, summary: str) -> str:
    return sha256(f"{category}|{source}|{normalize(summary)}")


def iso_parse(ts: str):
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None


# --------------------------------------------------------------------------
# Queue (Section 2) — atomic read-merge-write via temp + os.replace.
# --------------------------------------------------------------------------
def load_findings() -> list[dict]:
    p = _findings_jsonl()
    if not p.exists():
        return []
    out = []
    for line in p.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def merge_findings(existing: list[dict], raw: list[dict], now: str) -> list[dict]:
    """Apply Section 2.4 dedup rules. Returns the full ordered list to write."""
    merged = list(existing)
    index = {}
    for i, f in enumerate(merged):
        index.setdefault(f.get("dedup_key"), []).append(i)

    for r in raw:
        key = r["dedup_key"]
        last = iso_parse(now)
        matched = None
        for i in index.get(key, []):
            e = merged[i]
            if e.get("status") not in ("open", "digested"):
                continue
            ls = iso_parse(e.get("last_seen"))
            # Within STALE_WINDOW and still open/digested -> suppress append.
            if ls and last and (last - ls) < STALE_WINDOW:
                matched = i
                break

        if matched is not None:
            e = merged[matched]
            e["last_seen"] = now
            e["count"] = int(e.get("count", 1)) + 1
            e["evidence"] = r["evidence"]
            if r.get("summary") != e.get("summary"):
                e["summary"] = r["summary"]
        else:
            entry = dict(r)
            entry["status"] = "open"
            merged.append(entry)
            index.setdefault(key, []).append(len(merged) - 1)
    return merged


SCHEMA_HEADER = (
    "# system-doctor findings queue (JSONL, one object/line) — schema: "
    "id, ts, category, risk_tier, class, source, summary, evidence{type,ref,"
    "detail}, fix_suggestion, dedup_key, first_seen, last_seen, count, "
    "confidence, status. Consumed by US-159 orchestrator (Phase 2)."
)


def atomic_write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            f.write(SCHEMA_HEADER + "\n")
            for rec in records:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def atomic_write_json(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(obj, f, ensure_ascii=False, indent=2)
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


# --------------------------------------------------------------------------
# Probe helpers
# --------------------------------------------------------------------------
def _finding(category, tier, klass, source, summary, ev_type, ev_ref, ev_detail,
             fix_suggestion, now):
    """A raw finding awaiting dedup_key/ts materialization."""
    return {
        "category": category,
        "risk_tier": tier,
        "class": klass,
        "source": source,
        "summary": summary,
        "evidence": {"type": ev_type, "ref": ev_ref, "detail": ev_detail},
        "fix_suggestion": fix_suggestion,
    }


def _materialize(raw: dict, now: str) -> dict:
    d = dict(raw)
    d["ts"] = now
    d["dedup_key"] = dedup_key(d["category"], d["source"], d["summary"])
    d["id"] = d["dedup_key"]
    d["first_seen"] = now
    d["last_seen"] = now
    d["count"] = 1
    d["confidence"] = None
    d["status"] = "open"
    return d


def _read_jobs() -> dict:
    if not JOBS_JSON.exists():
        raise FileNotFoundError(f"jobs.json not readable: {JOBS_JSON}")
    return json.loads(JOBS_JSON.read_text())


def _output_has_file(job_id: str) -> bool:
    d = CRON_OUTPUT / job_id
    if d.is_dir() and any(d.iterdir()):
        return True
    # loose "<job_id>_<yyyyMMdd>_<hhmmss>.txt" full transcripts
    for p in CRON_OUTPUT.glob(f"{job_id}_*.txt"):
        return True
    return False


# --------------------------------------------------------------------------
# 1.1 Cron output & error logs
# --------------------------------------------------------------------------
def probe_cron(now: str) -> tuple[str, list[dict]]:
    data = _read_jobs()
    jobs = data.get("jobs", [])
    found: list[dict] = []

    for j in jobs:
        jid = j.get("id", "")
        name = j.get("name", "") or jid
        status = j.get("last_status")
        streak = int(j.get("failure_streak") or 0)
        last_error = (j.get("last_error") or "").strip()
        delivery_error = j.get("last_delivery_error")
        is_agent = not j.get("no_agent", False)

        # (a) last_status == "error" and streak >= 1
        if status == "error" and streak >= 1:
            is_dep = bool(_DEP_RE.search(last_error))
            tier = 1 if streak >= 3 else (0 if is_dep else 1)
            cause = "dependency/config" if is_dep else "code bug"
            found.append(_finding(
                "cron_error", tier, "issue", jid,
                f"{name} cron error",
                "cron_job", jid,
                f"last_status=error; failure_streak={streak}; cause={cause}; "
                f"last_error={_squash(last_error)}",
                f"{'Escalate: recurring failure needs code fix' if streak >= 3 else 'Re-run or re-pin interpreter (see US-163)'}",
                now))

        # (b) delivery error while status ok -> misroute (crosspost concern)
        if delivery_error and status == "ok":
            found.append(_finding(
                "cron_error", 0, "issue", jid,
                f"{name} delivery error",
                "cron_job", jid,
                f"last_delivery_error={_squash(delivery_error)}; last_status=ok",
                "Verify deliver-target / webhook routing",
                now))

        # (c) agent job with null/empty model field
        if is_agent and not (j.get("model") or "").strip():
            found.append(_finding(
                "cron_error", 0, "issue", jid,
                f"{name} missing model assignment",
                "cron_job", jid,
                "no_agent=false but model field null/empty",
                "Assign an explicit model tier (ADR-001)",
                now))

        # (d) enabled job with zero output files -> silent skip
        if j.get("enabled") and j.get("last_run_at") and not _output_has_file(jid):
            found.append(_finding(
                "cron_error", 1, "issue", jid,
                f"{name} silent skip (no output)",
                "cron_job", jid,
                "enabled job ran but output dir has zero files (no output != success)",
                "Investigate silent-skip; no output is not success",
                now))

    verdict = "finding" if found else "clean"
    return verdict, found


# --------------------------------------------------------------------------
# 1.2 Data freshness (DXY / yields / macro)
# --------------------------------------------------------------------------
def probe_data_freshness(now: str) -> tuple[str, list[dict]]:
    # D5 (resolved): a one-time read-only cache-path inventory must precede
    # real freshness checks. Until that inventory lands, this category reports
    # not_inspected rather than fabricating verdicts (anti false-clean).
    # No cache files are stat'd here; this emits a doctor_self blind-spot.
    found = [_finding(
        "doctor_self", 1, "issue", "data_freshness",
        "data_freshness cache-path inventory pending (D5)",
        "file_mtime", "N/A",
        "cache inventory (D5) not yet completed; category cannot issue a verdict",
        "Complete the one-time read-only cache-path + threshold inventory (D5)",
        now)]
    return "not_inspected", found


# --------------------------------------------------------------------------
# 1.3 Model staleness vs OpenRouter
# --------------------------------------------------------------------------
def probe_model_staleness(now: str) -> tuple[str, list[dict]]:
    data = _read_jobs()
    jobs = data.get("jobs", [])
    slugs = set()
    for j in jobs:
        m = (j.get("model") or "").strip()
        if m:
            slugs.add(m)
    if not slugs:
        return "clean", []

    models = _fetch_or_models()
    if models is None:
        # Network unavailable -> fail-closed, never "clean".
        found = [_finding(
            "doctor_self", 1, "issue", "model_staleness",
            "OpenRouter model list unreachable",
            "openrouter", "GET /v1/models",
            "could not verify pinned model slugs (network/proxy down)",
            "Fix proxy/network then re-scan model currency", now)]
        return "not_inspected", found

    known = {m.get("id", "") for m in models}
    found = []
    for slug in slugs:
        base = slug.split(":")[-1] if ":" in slug else slug
        # retired/404
        if slug not in known:
            # point-release heuristic: family present but exact suffix gone
            fam = re.sub(r"-\d{4,8}$", "", base)
            family_present = any(
                (fam and (m.startswith(fam))) for m in known)
            if family_present:
                found.append(_finding(
                    "model_staleness", 0, "optimization", slug,
                    f"newer point-release of {slug} exists",
                    "openrouter", slug,
                    f"family {fam} present; pinned suffix {base} superseded",
                    "Bump point-release (Phase 2 Tier-0)", now))
            else:
                found.append(_finding(
                    "model_staleness", 0, "issue", slug,
                    f"pinned model {slug} retired/404",
                    "openrouter", slug,
                    "slug not in OpenRouter model list",
                    "Re-pin to a live slug (routing decision)",
                    now))
    return ("finding" if found else "clean"), found


def _fetch_or_models():
    for url in OR_ENDPOINTS:
        try:
            req = Request(url, headers={"User-Agent": "HermesForge-SystemDoctor"})
            with urlopen(req, timeout=4) as r:
                data = json.loads(r.read())
            return data.get("data", [])
        except Exception:
            continue
    return None


# --------------------------------------------------------------------------
# 1.4 Cost drift vs ~$8/month cap
# --------------------------------------------------------------------------
def probe_cost(now: str) -> tuple[str, list[dict]]:
    if not USAGE_AUDIT.exists():
        return "not_inspected", [_finding(
            "doctor_self", 1, "issue", "cost_drift",
            "usage_audit.jsonl missing", "file_mtime", str(USAGE_AUDIT),
            "cost rollup source absent", "Restore usage audit", now)]

    cutoff = datetime.now(timezone.utc) - timedelta(days=COST_TRAILING_DAYS)
    per_model = {}
    unpriced = set()
    for line in USAGE_AUDIT.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            d = json.loads(line)
        except json.JSONDecodeError:
            continue
        ts = iso_parse(d.get("ts"))
        if not ts or ts.replace(tzinfo=timezone.utc) < cutoff:
            continue
        m = d.get("model") or "unknown"
        row = per_model.setdefault(m, {"prompt": 0, "completion": 0})
        row["prompt"] += int(d.get("prompt_tokens") or 0)
        row["completion"] += int(d.get("completion_tokens") or 0)
        if m not in MODEL_PRICE:
            unpriced.add(m)

    total_usd = 0.0
    for m, row in per_model.items():
        if m in MODEL_PRICE:
            pin, pout = MODEL_PRICE[m]
            total_usd += (row["prompt"] / 1e6) * pin + (row["completion"] / 1e6) * pout

    found = []
    if unpriced:
        found.append(_finding(
            "cost_drift", 1, "optimization", "usage_audit",
            "unpriced models in spend estimate",
            "file_mtime", str(USAGE_AUDIT),
            f"no price table entry for: {', '.join(sorted(unpriced))}",
            "Add pricing for unpriced models (spend estimate is partial)",
            now))
    if total_usd > COST_CAP_USD:
        found.append(_finding(
            "cost_drift", 1, "issue", "usage_audit",
            f"trailing-30d spend exceeds ${COST_CAP_USD} cap",
            "file_mtime", str(USAGE_AUDIT),
            f"estimated ${total_usd:.2f} over {COST_TRAILING_DAYS}d",
            "Investigate routing/tier spend (T2 decision in Phase 2)",
            now))

    return ("finding" if found else "clean"), found


# --------------------------------------------------------------------------
# 1.5 Disk / SSH / security posture
# --------------------------------------------------------------------------
def probe_disk_ssh(now: str) -> tuple[str, list[dict]]:
    found = []

    # disk
    try:
        u = shutil.disk_usage("/")
        pct = u.used / u.total * 100
        if pct > DISK_CRIT_PCT:
            found.append(_finding(
                "disk_ssh_security", 1, "issue", "df",
                f"disk usage {pct:.0f}% > {DISK_CRIT_PCT}%", "os_probe", "/",
                f"df / {pct:.1f}% used", "Cleanup (root cause may need eyes)", now))
        elif pct > DISK_WARN_PCT:
            found.append(_finding(
                "disk_ssh_security", 0, "optimization", "df",
                f"disk usage {pct:.0f}% ({DISK_WARN_PCT}-{DISK_CRIT_PCT}%)",
                "os_probe", "/", f"df / {pct:.1f}% used",
                "Monitor / pre-cleanup", now))
    except OSError as e:
        found.append(_finding(
            "doctor_self", 1, "issue", "df", f"disk probe failed: {e}",
            "os_probe", "/", "shutil.disk_usage raised", "Investigate", now))

    # core services (read-only status query)
    svcs = ("hermes-gateway", "hermesforge-listener", "ssh", "cron")
    for svc in svcs:
        try:
            r = subprocess.run(
                ["systemctl", "is-active", svc],
                capture_output=True, text=True, timeout=20)
            state = r.stdout.strip()
            if state != "active":
                found.append(_finding(
                    "disk_ssh_security", 1, "issue", f"systemd:{svc}",
                    f"service {svc} inactive ({state or r.stderr.strip() or 'unknown'})",
                    "os_probe", svc, f"systemctl is-active {svc} -> {state}",
                    "Restore service", now))
        except (OSError, subprocess.TimeoutExpired) as e:
            found.append(_finding(
                "doctor_self", 1, "issue", f"systemd:{svc}",
                f"service probe failed: {e}", "os_probe", svc,
                "systemctl is-active raised", "Investigate", now))

    # sshd effective config (security-relevant flags only)
    try:
        r = subprocess.run(["sshd", "-T"], capture_output=True, text=True,
                           timeout=20)
        eff = dict(
            (k, v) for k, v in
            (line.split(None, 1) for line in r.stdout.splitlines() if line and " " in line))
        for flag, label in (
            ("permitrootlogin", "PermitRootLogin"),
            ("passwordauthentication", "PasswordAuthentication")):
            val = eff.get(flag, "").lower()
            if val == "yes":
                found.append(_finding(
                    "disk_ssh_security", 2, "issue", f"sshd:{label}",
                    f"sshd {label} yes",
                    "os_probe", "sshd -T",
                    f"{label} yes broadens attack surface",
                    "Harden sshd (human-gated security decision)", now))
    except (OSError, subprocess.TimeoutExpired) as e:
        found.append(_finding(
            "doctor_self", 1, "issue", "sshd",
            f"sshd -T probe failed: {e}", "os_probe", "sshd -T",
            "sshd -T raised", "Investigate", now))

    return ("finding" if found else "clean"), found


# --------------------------------------------------------------------------
# 1.6 Upstream Hermes git (read-only; no pull/push/fetch-with-effect)
# --------------------------------------------------------------------------
def probe_git(now: str) -> tuple[str, list[dict]]:
    repo = HF_ROOT
    found = []

    def git(*args):
        return subprocess.run(
            ["git", "-C", str(repo), *args],
            capture_output=True, text=True, timeout=30)

    # dirty tree
    try:
        r = git("status", "--porcelain")
        dirty = [l for l in r.stdout.splitlines() if l.strip()]
        if dirty:
            # "persisting >24h": check file mtimes of changed paths
            old = 0
            for line in dirty:
                path = line[3:].split(" -> ")[-1].strip().strip('"')
                p = repo / path
                try:
                    mt = p.stat().st_mtime
                    if (datetime.now(timezone.utc).timestamp() - mt) > GIT_DIRTY_AGE.total_seconds():
                        old += 1
                except OSError:
                    pass
            if old > 0:
                found.append(_finding(
                    "upstream_git", 1, "issue", "git:dirty",
                    f"uncommitted changes persisting >24h ({old} file(s))",
                    "git_state", str(repo),
                    f"git status --porcelain: {len(dirty)} dirty; {old} persisting >24h",
                    "Commit changes immediately (hard rule)", now))
    except (OSError, subprocess.TimeoutExpired) as e:
        found.append(_finding(
            "doctor_self", 1, "issue", "git:dirty",
            f"git status failed: {e}", "git_state", str(repo),
            "git status raised", "Investigate", now))

    # ahead/behind/diverged vs local origin/main (no fetch)
    try:
        head = git("rev-parse", "HEAD").stdout.strip()
        origin = git("rev-parse", "origin/main").stdout.strip()
        if head and origin:
            ahead = git("rev-list", "--count", f"{origin}..{head}").stdout.strip()
            behind = git("rev-list", "--count", f"{head}..{origin}").stdout.strip()
            a = int(ahead or 0)
            b = int(behind or 0)
            if b > 0 and a == 0:
                found.append(_finding(
                    "upstream_git", 0, "issue", "git:remote",
                    f"local HEAD behind origin/main by {b}",
                    "git_state", str(repo),
                    f"behind={b} (unpulled upstream)",
                    "Pull upstream (Tier-0)", now))
            elif a > 0 and b > 0:
                found.append(_finding(
                    "upstream_git", 1, "issue", "git:remote",
                    f"diverged: ahead={a}, behind={b}",
                    "git_state", str(repo),
                    f"ahead={a} behind={b} (needs human-aware merge)",
                    "Human-aware merge required", now))
    except (OSError, subprocess.TimeoutExpired) as e:
        found.append(_finding(
            "doctor_self", 1, "issue", "git:remote",
            f"git remote position failed: {e}", "git_state", str(repo),
            "rev-parse/rev-list raised", "Investigate", now))

    # last commit age
    try:
        r = git("log", "-1", "--format=%ct")
        ts = int(r.stdout.strip())
        age = datetime.now(timezone.utc).timestamp() - ts
        if age > GIT_COMMIT_CADENCE.total_seconds():
            found.append(_finding(
                "upstream_git", 1, "optimization", "git:commit_age",
                f"last commit older than cadence ({age / 86400:.0f}d)",
                "git_state", str(repo),
                f"last commit {age / 86400:.1f} days old",
                "Commit pending work", now))
    except (OSError, subprocess.TimeoutExpired, ValueError) as e:
        found.append(_finding(
            "doctor_self", 1, "issue", "git:commit_age",
            f"git log failed: {e}", "git_state", str(repo),
            "git log raised", "Investigate", now))

    return ("finding" if found else "clean"), found


# --------------------------------------------------------------------------
# Orchestrator
# --------------------------------------------------------------------------
PROBES = {
    "cron_error": probe_cron,
    "data_freshness": probe_data_freshness,
    "model_staleness": probe_model_staleness,
    "cost_drift": probe_cost,
    "disk_ssh_security": probe_disk_ssh,
    "upstream_git": probe_git,
}


def run_scan(now: str | None = None) -> dict:
    """Run all probes, merge into queue, write state. Returns state obj."""
    now = now or now_iso()
    raw_findings: list[dict] = []
    category_verdicts: dict[str, dict] = {}

    for cat, probe in PROBES.items():
        try:
            verdict, findings = probe(now)
        except Exception as e:  # noqa: BLE001 — a crash is a finding, never clean
            verdict = "error"
            findings = [_finding(
                "doctor_self", 1, "issue", cat,
                f"{cat} probe crashed: {type(e).__name__}: {e}",
                "doctor_self", cat, f"probe raised {type(e).__name__}",
                "Investigate collector probe", now)]
        if verdict not in VERDICTS:
            verdict = "error"
        category_verdicts[cat] = {
            "verdict": verdict,
            "last_verdict_ts": now,
        }
        raw_findings.extend(findings)

    materialized = [_materialize(r, now) for r in raw_findings]
    existing = load_findings()
    merged = merge_findings(existing, materialized, now)
    atomic_write_jsonl(_findings_jsonl(), merged)

    state = {
        "last_full_scan_ts": now,
        "stale_window_hours": int(STALE_WINDOW.total_seconds() // 3600),
        "categories": category_verdicts,
    }
    atomic_write_json(_state_json(), state)
    return state


def main() -> int:
    state = run_scan()
    n = len(load_findings())
    print(json.dumps({
        "scan": "complete",
        "last_full_scan_ts": state["last_full_scan_ts"],
        "total_findings": n,
        "categories": state["categories"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())