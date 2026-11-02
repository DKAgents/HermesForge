#!/usr/bin/env python3
"""
cron_watchdog.py — US-194 artifact-based cron watchdog.

Verifies REAL job output artifacts (file mtimes, row counts, non-empty
error-free stdout) instead of `last_status` (which agent-wrapped crons lie
about — the agent reports its own exit, not the subprocess it shelled to).

On any job failing its artifact check for a persistent streak >= 2, posts a
Discord alert (to the source-server strategy-status channel) carrying the
ACTUAL error extracted from the job's own output. Alerting is EDGE-triggered:
a given failure streak alerts ONCE (when it first reaches the threshold), not
on every subsequent tick, and only re-alerts on a CHANGE (the streak resolves,
or a NEW streak begins).

Why: the Daily Signal Scanner failed for 29 straight days because its artifact
(the .md output) carried a pyarrow ImportError while `last_status`/`failure_streak`
only reflected the wrapper exit. Artifact + streak detection alerts on day 2.

Streak state is persisted in ~/.hermes/cron/watchdog_streaks.json so a transient
blip does not alert and a real failure escalates on the second consecutive miss.
"""

import json
import os
import pathlib
import re
import time
import urllib.request
from typing import Optional

HOME = pathlib.Path.home()
CRON_OUTPUT = HOME / ".hermes" / "cron" / "output"
JOBS_FILE = HOME / ".hermes" / "cron" / "jobs.json"
STATE_FILE = HOME / ".hermes" / "cron" / "watchdog_streaks.json"

# Discord strategy-status channel (source server) — matches the prior watchdog.
ALERT_CHANNEL_ID = os.environ.get("STRATEGY_STATUS_CHANNEL_ID", "1533332485641998386")

# Error signatures that mark a run as unhealthy even if its file is non-empty.
ERROR_SIGNATURES = (
    "Traceback (most recent call last)",
    "ModuleNotFoundError",
    "ImportError",
    "Unable to find a usable engine",   # pyarrow / fastparquet missing
    "Script exited with code",
    "parquet support",
    "SyntaxError",
    "KeyError:",
)

# ── Monitored jobs: artifact spec per job_id ────────────────────────────────
# max_age_m = maximum tolerated age of the newest output artefact (minutes).
# data_files = optional extra artifacts that must also be fresh AND carry a
#   real row-count / signature (proof the job wrote DATA, not just an empty
#   .md) — see _check_job for the row-count + no-regression comparison.
# NOTE (US-191 reconcile): STR-Q Intraday Sweep (b9fb0afb1e29) is NOT monitored
#   — US-191 stopped its capture, so its only output is a permanent BLOCK
#   marker, not a real scan. Monitoring it would false-alert "stale" once its
#   cron is disabled.
MONITORED = {
    "3f49a07a2f04": {"name": "Daily Signal Scanner", "max_age_m": 22 * 60, "glob": "*.md"},
    "4b178ecc02cd": {"name": "Paper Trading Capture (A/B/D)", "max_age_m": 22 * 60, "glob": "*.md"},
    "e3c306f58545": {"name": "Daily F&G Fetch", "max_age_m": 25 * 60, "glob": "*.md",
                     "data_files": [HOME / ".hermes" / "market_data" / "fear_greed.parquet"]},
    # The digest's JOB is to report system errors, so its output legitimately
    # contains error text; rely on freshness/non-empty, not error-signature.
    "de5f707d1495": {"name": "Confidence Digest", "max_age_m": 25 * 60, "glob": "*.md",
                     "check_content": False},
}

ALERT_THRESHOLD = 2


def _load_env():
    env_file = HOME / ".hermes" / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text(errors="replace").splitlines():
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def _post_discord(content: str) -> bool:
    token = os.environ.get("DISCORD_BOT_TOKEN", "")
    if not token:
        return False
    payload = json.dumps({"content": content}).encode()
    req = urllib.request.Request(
        f"https://discord.com/api/v10/channels/{ALERT_CHANNEL_ID}/messages",
        data=payload,
        headers={"Authorization": f"Bot {token}",
                 "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=10):
            return True
    except Exception:
        return False


def _newest_file(job_id: str, pattern: str):
    d = CRON_OUTPUT / job_id
    if not d.is_dir():
        return None
    files = sorted(d.glob(pattern), key=lambda p: p.stat().st_mtime)
    return files[-1] if files else None


def _extract_error(text: str) -> str:
    """Pull a short, actionable error line from raw output."""
    m = re.search(r"(ImportError:.*)", text)
    if m:
        return m.group(1).strip()[:400]
    if "Unable to find a usable engine" in text:
        return "pandas parquet engine missing (pyarrow/fastparquet not installed)"
    lines = [ln for ln in text.splitlines() if ln.strip()]
    for ln in reversed(lines):
        if re.search(r"(Error|error|Traceback|Exception)", ln):
            return ln.strip()[:400]
    return "\n".join(lines[-6:]).strip()[:400]


def _has_error_signature(text: str) -> bool:
    return any(sig in text for sig in ERROR_SIGNATURES)


def _artifact_signature(path) -> dict:
    """Return {'rows': int|None, 'size': int, 'mtime': int} — the data identity
    of an artifact.

    'rows' is the real row count for tabular files we know how to read (parquet
    via metadata — cheap, no full load; csv via line count). 'size'/'mtime' are
    the fallback signature for any other file type. A non-None 'rows' enables
    the row-count + no-regression checks in _check_job.
    """
    p = pathlib.Path(path)
    st = p.stat()
    sig = {"rows": None, "size": int(st.st_size), "mtime": int(st.st_mtime)}
    try:
        if p.suffix in (".parquet", ".pq"):
            import pyarrow.parquet as pq
            sig["rows"] = int(pq.ParquetFile(str(p)).metadata.num_rows)
        elif p.suffix == ".csv":
            with open(p, "r", errors="replace") as fh:
                sig["rows"] = sum(1 for _ in fh)
    except Exception:
        sig["rows"] = None
    return sig


def _check_job(job_id: str, spec: dict, prev_sigs: dict) -> dict:
    """Return {'ok': bool, 'error': str, 'data_sigs': dict}. Artifact-based,
    not last_status.

    prev_sigs: the last-GOOD data signatures (path -> signature dict) persisted
    in state, used for the row-count / no-regression comparison. Only updated
    (via the returned data_sigs) when the job is healthy, so regression is
    always measured against the last known-good run.
    """
    data_sigs = {}
    f = _newest_file(job_id, spec["glob"])
    if f is None:
        return {"ok": False, "error": f"no output artifact under {CRON_OUTPUT}/{job_id}",
                "data_sigs": data_sigs}

    age_m = (time.time() - f.stat().st_mtime) / 60.0
    if age_m > spec["max_age_m"]:
        return {"ok": False, "error": f"artifact stale ({age_m:.0f}m old > {spec['max_age_m']}m): {f.name}",
                "data_sigs": data_sigs}

    text = f.read_text(errors="replace")
    if len(text.strip()) < 10:
        return {"ok": False, "error": f"empty output: {f.name}", "data_sigs": data_sigs}
    if spec.get("check_content", True) and _has_error_signature(text):
        return {"ok": False, "error": _extract_error(text), "data_sigs": data_sigs}

    for extra in spec.get("data_files", []):
        if not extra.exists():
            return {"ok": False, "error": f"missing data artifact: {extra}",
                    "data_sigs": data_sigs}
        if (time.time() - extra.stat().st_mtime) / 60.0 > spec["max_age_m"]:
            return {"ok": False, "error": f"stale data artifact: {extra}",
                    "data_sigs": data_sigs}

        sig = _artifact_signature(extra)

        # Row-count proof: the job must have actually WRITTEN data, not just
        # (re)created an empty/zero-row file (fresh mtime alone can't tell).
        if sig["rows"] is not None and sig["rows"] == 0:
            return {"ok": False, "error": f"data artifact is empty (0 rows): {extra}",
                    "data_sigs": data_sigs}

        # Artifact-signature comparison: detect a REGRESSION vs the last-good
        # run (row count shrank = silent data loss / truncation).
        prev = prev_sigs.get(str(extra))
        if (prev is not None and prev.get("rows") is not None
                and sig["rows"] is not None and sig["rows"] < prev["rows"]):
            return {"ok": False,
                    "error": f"data artifact REGRESSED {prev['rows']} -> {sig['rows']} rows: {extra}",
                    "data_sigs": data_sigs}

        data_sigs[str(extra)] = sig

    return {"ok": True, "error": "", "data_sigs": data_sigs}


def _load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def _save_state(state: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = STATE_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, indent=2))
    tmp.replace(STATE_FILE)


def main() -> int:
    _load_env()

    # Read jobs.json only to attach names to ids (never for failure detection).
    name_by_id = {}
    if JOBS_FILE.exists():
        try:
            jobs = json.loads(JOBS_FILE.read_text()).get("jobs", [])
            if isinstance(jobs, dict):
                jobs = list(jobs.values())
            for j in jobs:
                name_by_id[j.get("id", "")] = j.get("name", "")
        except (json.JSONDecodeError, OSError):
            pass

    state = _load_state()
    alerts = []     # (name, job_id, streak, error) — new failure streaks >= threshold
    resolved = []   # name — streaks that just recovered

    for job_id, spec in MONITORED.items():
        prev = state.get(job_id, {})
        prev_sigs = prev.get("data_sigs", {})
        check = _check_job(job_id, spec, prev_sigs)
        name = spec["name"]

        if check["ok"]:
            # Only announce a recovery if we had previously ALERTED on this
            # streak (avoid spamming "resolved" for jobs that were never broken).
            was_alerted = (int(prev.get("streak", 0)) >= ALERT_THRESHOLD
                           and bool(prev.get("alerted", False)))
            state[job_id] = {"streak": 0, "last_error": "", "alerted": False,
                             "data_sigs": check.get("data_sigs", {})}
            if was_alerted:
                resolved.append(name)
            continue

        streak = int(prev.get("streak", 0)) + 1
        already_alerted = bool(prev.get("alerted", False))
        # On failure, keep the last-GOOD data signatures (do not advance the
        # baseline) so a real data regression is still detected next tick.
        state[job_id] = {"streak": streak, "last_error": check["error"],
                         "alerted": already_alerted, "data_sigs": prev_sigs}

        # Alert ONCE per streak (edge-triggered), not on every subsequent tick
        # of the SAME unresolved streak.
        if streak >= ALERT_THRESHOLD and not already_alerted:
            alerts.append((name, job_id, streak, check["error"]))
            state[job_id]["alerted"] = True

    _save_state(state)

    if alerts or resolved:
        lines = ["**Watchdog Alert — artifact failure streak ≥ 2**"]
        for name, job_id, streak, err in alerts:
            lines.append(f"- **{name}** (`{job_id[:8]}`) — streak {streak}\n"
                         f"  error: `{err[:300]}`")
        for name in resolved:
            lines.append(f"- ✅ **{name}** — recovered (failure streak cleared)")
        _post_discord("\n".join(lines))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())