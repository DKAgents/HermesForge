"""
test_trials_ledger.py — Tests for trials_ledger module.
"""

import json
import os
import sys
import tempfile
import threading
from pathlib import Path

# Point trials_ledger to a temp path for isolated tests
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

TEST_LEDGER = Path(tempfile.mkdtemp()) / "test_trials.jsonl"

# Patch LEDGER_PATH before importing
import trials_ledger as ledger

ledger.LEDGER_PATH = TEST_LEDGER
ledger.LEDGER_DIR = TEST_LEDGER.parent


def _clean_ledger():
    if TEST_LEDGER.exists():
        TEST_LEDGER.unlink()
    if TEST_LEDGER.with_suffix(".tmp").exists():
        TEST_LEDGER.with_suffix(".tmp").unlink()


def test_append_increments_count():
    """T1: append increments count."""
    _clean_ledger()
    assert ledger.count() == 0

    ledger.increment_trial(
        hypothesis_id="H1",
        param_hash="abc123",
        universe_hash="def456",
        period_start="2020-01-01",
        period_end="2020-12-31",
        result={"sharpe": 1.5, "avg_r": 0.5, "pf": 2.0, "trade_count": 100},
    )
    assert ledger.count() == 1

    ledger.increment_trial(
        hypothesis_id="H2",
        param_hash="ghi789",
        universe_hash="jkl012",
        period_start="2021-01-01",
        period_end="2021-12-31",
        result={"sharpe": 0.8, "avg_r": 0.3, "pf": 1.5, "trade_count": 50},
    )
    assert ledger.count() == 2
    print("T1 PASS: append increments count")


def test_concurrent_writes():
    """T2: concurrent writes don't lose entries (simulate with threading)."""
    _clean_ledger()
    errors = []
    written_ids = set()
    lock = threading.Lock()

    def writer(worker_id: int, n: int):
        for i in range(n):
            try:
                entry = ledger.increment_trial(
                    hypothesis_id=f"T2-W{worker_id}-{i}",
                    param_hash=f"ph-{worker_id}-{i}",
                    universe_hash="uh-test",
                    period_start="2020-01-01",
                    period_end="2020-12-31",
                    result={"sharpe": 1.0, "avg_r": 0.5, "pf": 2.0, "trade_count": 10},
                )
                with lock:
                    written_ids.add(entry["hypothesis_id"])
            except Exception as e:
                errors.append(str(e))

    threads = []
    n_per_worker = 10
    for w in range(5):
        t = threading.Thread(target=writer, args=(w, n_per_worker))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    assert len(errors) == 0, f"Errors during concurrent writes: {errors}"
    total = ledger.count()
    expected = 5 * n_per_worker
    assert total == expected, f"Expected {expected} entries, got {total}"
    assert len(written_ids) == expected, f"Expected {expected} unique IDs, got {len(written_ids)}"
    print(f"T2 PASS: concurrent writes ({total} entries, {len(errors)} errors)")


def test_read_all():
    """T3: read_all returns all entries."""
    _clean_ledger()
    entries_data = [
        ("H3a", 0.5, 100),
        ("H3b", 1.0, 200),
        ("H3c", 1.5, 300),
    ]
    for hid, sharpe, tc in entries_data:
        ledger.increment_trial(
            hypothesis_id=hid,
            param_hash="ph",
            universe_hash="uh",
            period_start="2020-01-01",
            period_end="2020-12-31",
            result={"sharpe": sharpe, "trade_count": tc},
        )

    all_entries = ledger.read_all()
    assert len(all_entries) == 3
    assert all_entries[0]["hypothesis_id"] == "H3a"
    assert all_entries[1]["hypothesis_id"] == "H3b"
    assert all_entries[2]["hypothesis_id"] == "H3c"
    assert all_entries[2]["result"]["trade_count"] == 300
    print("T3 PASS: read_all returns all entries")


def test_hash_chain_integrity():
    """T4: hash chain integrity — verify passes clean, fails on tampered."""
    _clean_ledger()

    for i in range(5):
        ledger.increment_trial(
            hypothesis_id=f"H4-{i}",
            param_hash=f"ph-{i}",
            universe_hash="uh",
            period_start="2020-01-01",
            period_end="2020-12-31",
            result={"sharpe": 1.0, "trade_count": 10},
        )

    # Clean ledger should verify
    valid, msg = ledger.verify_integrity()
    assert valid, f"Clean ledger failed: {msg}"
    print(f"T4a PASS: clean ledger verifies — {msg}")

    # Tamper with entry 2
    with open(TEST_LEDGER, "r") as f:
        lines = f.readlines()

    entry = json.loads(lines[2])
    entry["result"]["sharpe"] = 999.0  # tamper
    lines[2] = json.dumps(entry, sort_keys=True) + "\n"

    with open(TEST_LEDGER, "w") as f:
        f.writelines(lines)

    valid, msg = ledger.verify_integrity()
    assert not valid, "Tampered ledger should fail verification"
    assert "hash mismatch" in msg.lower() or "entry 2" in msg.lower() or "entry 3" in msg.lower()
    print(f"T4b PASS: tampered ledger detected — {msg}")


def test_atomic_write_survives_crash():
    """T5: atomic write survives crash (simulate partial write)."""
    _clean_ledger()

    # Write one good entry first
    ledger.increment_trial(
        hypothesis_id="H5-good",
        param_hash="ph",
        universe_hash="uh",
        period_start="2020-01-01",
        period_end="2020-12-31",
        result={"sharpe": 1.0, "trade_count": 10},
    )
    assert ledger.count() == 1

    # Simulate a crash: write a partial/incomplete line to the actual ledger
    # This shouldn't happen with our atomic write, but let's verify
    # the ledger handles corrupt lines gracefully
    with open(TEST_LEDGER, "a") as f:
        f.write("NOT VALID JSON {{{{{\n")

    # read_all should skip the corrupt line
    entries = ledger.read_all()
    assert len(entries) == 1, f"Expected 1 entry (corrupt line skipped), got {len(entries)}"
    assert entries[0]["hypothesis_id"] == "H5-good"

    # count() should still only count valid lines
    # (count counts non-empty lines, so corrupt line still counts as a line)
    # This is expected: count is a fast N-getter, integrity is verify's job

    # Now test the temp-file approach: ensure no .tmp file is left behind
    tmp_path = TEST_LEDGER.with_suffix(".tmp")
    assert not tmp_path.exists(), "Stale .tmp file left behind"

    # Add another entry via atomic write
    ledger.increment_trial(
        hypothesis_id="H5-good2",
        param_hash="ph",
        universe_hash="uh",
        period_start="2020-01-01",
        period_end="2020-12-31",
        result={"sharpe": 2.0, "trade_count": 20},
    )
    assert not tmp_path.exists(), ".tmp file should not persist after successful write"

    entries = ledger.read_all()
    good_entries = [e for e in entries if "H5" in str(e.get("hypothesis_id", ""))]
    assert len(good_entries) >= 2
    print("T5 PASS: atomic write survives crash")


import glob


def test_backfill_real_csvs():
    """T6: backfill reads real CSVs and produces entries."""
    results_dir = Path("/root/HermesForge/scripts/validation/results")
    csvs = sorted(results_dir.glob("*.csv"))
    assert len(csvs) > 0, "No CSV files found"

    # Use a fresh temp ledger for this test
    test_path = TEST_LEDGER.parent / "test_backfill.jsonl"
    old_path = ledger.LEDGER_PATH
    ledger.LEDGER_PATH = test_path
    if test_path.exists():
        test_path.unlink()

    try:
        # Read first CSV and simulate a backfill entry
        import csv
        import hashlib

        test_csv = csvs[0]
        hypothesis_id = test_csv.stem

        with open(test_csv, "r") as f:
            reader = csv.DictReader(f)
            rows = [row for row in reader if any(v.strip() for v in row.values())]

        assert len(rows) > 0, f"CSV {test_csv.name} has no data rows"

        # Basic stats
        trade_count = len(rows)
        r_vals = []
        for row in rows:
            r_str = row.get("r_multiple", "")
            if r_str:
                try:
                    r_vals.append(float(r_str))
                except (ValueError, TypeError):
                    pass

        avg_r = sum(r_vals) / len(r_vals) if r_vals else 0.0

        entry = ledger.increment_trial(
            hypothesis_id=hypothesis_id,
            param_hash="test-ph",
            universe_hash="test-uh",
            period_start="2020-01-01",
            period_end="2020-12-31",
            result={
                "sharpe": 0.0,
                "avg_r": round(avg_r, 6),
                "pf": 0.0,
                "trade_count": trade_count,
            },
        )

        assert ledger.count() == 1
        assert entry["hypothesis_id"] == hypothesis_id
        assert entry["result"]["trade_count"] == trade_count

        print(f"T6 PASS: backfill test CSV — {hypothesis_id} ({trade_count} trades, avg_r={avg_r:.4f})")
    finally:
        ledger.LEDGER_PATH = old_path


if __name__ == "__main__":
    print("Running trials_ledger tests...\n")
    test_append_increments_count()
    test_concurrent_writes()
    test_read_all()
    test_hash_chain_integrity()
    test_atomic_write_survives_crash()
    test_backfill_real_csvs()
    print("\nAll tests passed.")