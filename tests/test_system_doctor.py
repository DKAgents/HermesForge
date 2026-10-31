"""Tests for the Phase-1 system-doctor collector (US-158).

Scoped to the two hard acceptance criteria in the spec / implementation order:

  1. The collector DETECTS the three known-failing cron jobs (Section 1.1
     "known live exemplars"):
       - b9fb0afb1e29  STR-Q Intraday Sweep (pandas)
       - 3f49a07a2f04  Daily Signal Scanner (mplfinance)
       - 232975d5fc83  Connection Discovery (yaml)

  2. Re-running the collector produces ZERO duplicates (Section 2.4 dedup:
     sha256 key + STALE_WINDOW suppression -> count increments, no new rows).

Both assertions run against the LIVE jobs.json (read-only) but a throwaway
cache dir, so the production findings.jsonl is never touched by tests.
"""

import importlib.util
import json
import os
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# Import the collector without executing its __main__.
_SPEC = importlib.util.spec_from_file_location(
    "collector", str(REPO / "scripts" / "system_doctor" / "collector.py"))
collector = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(collector)

KNOWN_FAILING_JOBS = {
    "b9fb0afb1e29": "pandas",
    "3f49a07a2f04": "mplfinance",
    "232975d5fc83": "yaml",
}


def _overrides(tmp: str) -> dict:
    """Point the collector at a throwaway cache dir; keep live read sources."""
    return {
        "SYSTEM_DOCTOR_CACHE": str(Path(tmp) / "cache"),
        # default read sources (jobs.json etc.) remain the live ones
    }


def _run(tmp: str):
    os.environ["SYSTEM_DOCTOR_CACHE"] = str(Path(tmp) / "cache")
    state = collector.run_scan()
    findings_file = Path(os.environ["SYSTEM_DOCTOR_CACHE"]) / "findings.jsonl"
    findings = []
    if findings_file.exists():
        for line in findings_file.read_text().splitlines():
            if line.strip() and not line.startswith("#"):
                findings.append(json.loads(line))
    return state, findings


def test_detects_three_known_failing_jobs():
    with tempfile.TemporaryDirectory() as tmp:
        _run(tmp)
        # Re-read via the module's loader (paths are set by env at call time)
        _, findings = _run(tmp)

        detected = {
            f.get("source"): f
            for f in findings
            if f.get("category") == "cron_error" and f.get("evidence", {}).get("type") == "cron_job"
        }

        for jid, dep in KNOWN_FAILING_JOBS.items():
            assert jid in detected, (
                f"collector failed to detect failing job {jid} (expected "
                f"{dep} failure signature)")
            f = detected[jid]
            assert f["risk_tier"] in (0, 1, 2), "risk_tier out of enum"
            assert f["class"] == "issue"
            assert f["status"] == "open"
            assert "error" in f["evidence"]["detail"].lower() or \
                f["summary"].lower().endswith("cron error")


def test_rerun_produces_zero_duplicates():
    with tempfile.TemporaryDirectory() as tmp:
        os.environ["SYSTEM_DOCTOR_CACHE"] = str(Path(tmp) / "cache")

        # First run.
        collector.run_scan()
        p1 = Path(os.environ["SYSTEM_DOCTOR_CACHE"]) / "findings.jsonl"
        first = [json.loads(l) for l in p1.read_text().splitlines()
                 if l.strip() and not l.startswith("#")]
        keys1 = {f["dedup_key"] for f in first}

        # Second run (idempotent re-run).
        collector.run_scan()
        p2 = Path(os.environ["SYSTEM_DOCTOR_CACHE"]) / "findings.jsonl"
        second = [json.loads(l) for l in p2.read_text().splitlines()
                  if l.strip() and not l.startswith("#")]
        keys2 = {f["dedup_key"] for f in second}

        # No new dedup keys => no duplicate rows materialized.
        assert keys2 == keys1, (
            f"re-run changed the finding set: {keys2 ^ keys1}")

        # Counts must have incremented (suppressed append), not duplicated.
        by_key = {}
        for f in second:
            by_key[f["dedup_key"]] = by_key.get(f["dedup_key"], 0) + 1
        assert all(v == 1 for v in by_key.values()), \
            "duplicate rows found after re-run (dedup failed)"
        for f in second:
            if f["category"] == "cron_error" and f["source"] in KNOWN_FAILING_JOBS:
                assert f["count"] >= 2, "dedup should have incremented count"


def test_state_file_written_and_categories_populated():
    with tempfile.TemporaryDirectory() as tmp:
        os.environ["SYSTEM_DOCTOR_CACHE"] = str(Path(tmp) / "cache")
        state = collector.run_scan()
        assert state.get("last_full_scan_ts"), "state must record last_full_scan_ts"
        assert set(state["categories"]) == set(collector.CATEGORIES), \
            "all six categories must have a verdict"
        for cat, info in state["categories"].items():
            assert info["verdict"] in collector.VERDICTS
            assert info.get("last_verdict_ts")


if __name__ == "__main__":
    # Allow running directly with a lightweight harness (no pytest dependency).
    import traceback
    tests = [
        test_detects_three_known_failing_jobs,
        test_rerun_produces_zero_duplicates,
        test_state_file_written_and_categories_populated,
    ]
    failed = 0
    for t in tests:
        try:
            t()
            print(f"PASS {t.__name__}")
        except AssertionError as e:
            failed += 1
            print(f"FAIL {t.__name__}: {e}")
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"ERROR {t.__name__}: {type(e).__name__}: {e}")
            traceback.print_exc()
    print(f"\n{len(tests) - failed}/{len(tests)} passed")
    sys.exit(1 if failed else 0)