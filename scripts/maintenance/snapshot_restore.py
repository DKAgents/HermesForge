#!/usr/bin/env python3
"""
snapshot_restore.py — US-126: Daily snapshots + off-box copy + weekly restore drill

Snapshots the trade journal and derived trades.csv daily. Retains ≥35 days
on-box. Optionally copies to an off-VPS destination. Runs a weekly restore
drill that reconstructs trades.csv from the journal and diffs against live.

Usage:
    python3 snapshot_restore.py --snapshot           # create today's snapshot
    python3 snapshot_restore.py --restore-drill       # reconstruct + diff
    python3 snapshot_restore.py --manifest            # print manifest
    python3 snapshot_restore.py --prune               # remove snapshots >35d

Environment (for off-box copy):
    OFFSITE_BACKUP_PATH=/mnt/backup or s3://bucket/prefix or scp://host/path
    (configured via .env, never hardcoded — falls back to skipping copy)
"""

import hashlib
import json
import os
import pathlib
import shutil
import subprocess
import sys
import datetime
from typing import Optional

# ── Paths ────────────────────────────────────────────────────────────────────

REPO_ROOT = pathlib.Path(__file__).parent.parent.parent
PAPER_DIR = REPO_ROOT / "scripts" / "paper_trading"
sys.path.insert(0, str(PAPER_DIR))  # for trade_journal import
JOURNAL_PATH = PAPER_DIR / "trade_journal.jsonl"
CSV_PATH = PAPER_DIR / "trades.csv"
MANIFEST_PATH = PAPER_DIR / "trade_journal_manifest.txt"

CROSSPOST_STATE_PATH = pathlib.Path("/root/.hermes/crosspost_state.json")

SNAPSHOT_DIR = PAPER_DIR / "snapshots"
SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)

DATA_MANIFEST_PATH = REPO_ROOT / "reports" / "campaigns" / "2026-09-aegis-rebuild" / "data-manifest.md"

RETENTION_DAYS = 35

# Pacific Time display
PACIFIC = datetime.timezone(datetime.timedelta(hours=-7))  # PDT


# ── Helpers ───────────────────────────────────────────────────────────────────

def sha256_file(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _now_pt() -> str:
    return datetime.datetime.now(PACIFIC).strftime("%Y-%m-%d %H:%M:%S %Z")


def _today_str() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d")


def _manifest_record() -> dict:
    """Read the trade journal manifest if it exists."""
    if not MANIFEST_PATH.exists():
        return {}
    record = {}
    with open(MANIFEST_PATH) as f:
        for line in f:
            k, _, v = line.partition(": ")
            record[k.strip()] = v.strip()
    return record


# ── Snapshot ─────────────────────────────────────────────────────────────────

def create_snapshot() -> dict:
    """Create a timestamped, checksummed snapshot archive."""
    today = _today_str()
    prefix = SNAPSHOT_DIR / f"snapshot-{today}"

    result = {
        "date": today,
        "journal_sha256": "",
        "csv_sha256": "",
        "crosspost_state_sha256": "",
        "crosspost_state_bytes": 0,
        "journal_rows": 0,
        "manifest": {},
        "offbox_copied": False,
    }

    if not JOURNAL_PATH.exists():
        result["error"] = "journal not found — nothing to snapshot"
        return result

    # Checksums
    result["journal_sha256"] = sha256_file(JOURNAL_PATH)
    if CSV_PATH.exists():
        result["csv_sha256"] = sha256_file(CSV_PATH)
    if CROSSPOST_STATE_PATH.exists():
        result["crosspost_state_sha256"] = sha256_file(CROSSPOST_STATE_PATH)
        result["crosspost_state_bytes"] = CROSSPOST_STATE_PATH.stat().st_size
    result["manifest"] = _manifest_record()

    # Count journal rows
    with open(JOURNAL_PATH) as f:
        result["journal_rows"] = sum(1 for _ in f if _.strip())

    # Create archive: copy journal + CSV + manifest into snapshot dir
    snap_dir = pathlib.Path(str(prefix) + ".d")
    snap_dir.mkdir(parents=True, exist_ok=True)

    try:
        shutil.copy2(JOURNAL_PATH, snap_dir / "trade_journal.jsonl")
        if CSV_PATH.exists():
            shutil.copy2(CSV_PATH, snap_dir / "trades.csv")
        if MANIFEST_PATH.exists():
            shutil.copy2(MANIFEST_PATH, snap_dir / "manifest.txt")
        if CROSSPOST_STATE_PATH.exists():
            shutil.copy2(CROSSPOST_STATE_PATH, snap_dir / "crosspost_state.json")

        # Write snapshot metadata
        meta = snap_dir / "snapshot.json"
        with open(meta, "w") as f:
            json.dump(result, f, indent=2)

        print(f"Snapshot created: {snap_dir.name}")
        print(f"  journal: {result['journal_rows']} rows, sha256={result['journal_sha256'][:16]}...")
        print(f"  csv: sha256={result['csv_sha256'][:16]}...")
        if result["crosspost_state_bytes"]:
            print(f"  crosspost_state: {result['crosspost_state_bytes']} bytes, sha256={result['crosspost_state_sha256'][:16]}...")
    except Exception as e:
        result["error"] = str(e)
        print(f"Snapshot FAILED: {e}")

    # Off-box copy
    result["offbox_copied"] = _copy_offsite(snap_dir)

    return result


def _copy_offsite(snap_dir: pathlib.Path) -> bool:
    """Copy snapshot to off-VPS destination if configured."""
    dest = os.environ.get("OFFSITE_BACKUP_PATH", "")
    if not dest:
        return False

    try:
        if dest.startswith("scp://"):
            # scp://host/path → scp -r <snap_dir> <host>:<path>/
            target = dest[6:]  # strip scp://
            subprocess.run(
                ["scp", "-r", "-q", str(snap_dir), target],
                timeout=60, check=True
            )
        elif dest.startswith("s3://"):
            # s3://bucket/prefix → aws s3 cp
            subprocess.run(
                ["aws", "s3", "cp", "--recursive", str(snap_dir), f"{dest}/{snap_dir.name}/"],
                timeout=120, check=True
            )
        elif dest.startswith("/"):
            # Local path (different mount point)
            target = pathlib.Path(dest) / snap_dir.name
            shutil.copytree(snap_dir, target, dirs_exist_ok=True)
        else:
            print(f"  ⚠️ Unknown offsite destination scheme: {dest[:30]}...")
            return False

        print(f"  Off-box: copied to {dest}")
        return True
    except Exception as e:
        print(f"  ⚠️ Off-box copy failed: {e}")
        return False


# ── Restore Drill ────────────────────────────────────────────────────────────

def run_restore_drill() -> dict:
    """Reconstruct trades.csv from the journal and diff against live."""
    result = {
        "date": _today_str(),
        "journal_rows": 0,
        "restored_rows": 0,
        "live_csv_rows": 0,
        "match": False,
        "diffs": [],
    }

    if not JOURNAL_PATH.exists():
        result["error"] = "journal not found"
        return result

    with open(JOURNAL_PATH) as f:
        result["journal_rows"] = sum(1 for _ in f if _.strip())

    # Reconstruct CSV from journal (uses in-memory replay, never touches live)
    import tempfile

    tmpdir = pathlib.Path(tempfile.mkdtemp())
    tmp_csv = tmpdir / "trades.csv"

    try:
        # Rebuild to temp path
        from trade_journal import rebuild_csv
        result["restored_rows"] = rebuild_csv(tmp_csv)

        # Diff against live CSV (normalize line endings for comparison)
        if CSV_PATH.exists():
            with open(CSV_PATH) as f:
                live_lines = [l.rstrip('\r\n') for l in f]
            with open(tmp_csv) as f:
                restored_lines = [l.rstrip('\r\n') for l in f]
            result["live_csv_rows"] = len(live_lines) - 1  # minus header

            if live_lines == restored_lines:
                result["match"] = True
                print(f"✅ Restore drill PASSED: {result['restored_rows']} rows match live")
            else:
                result["match"] = False
                # Find differing rows
                for i, (a, b) in enumerate(zip(live_lines, restored_lines)):
                    if a != b:
                        result["diffs"].append({"line": i, "live": a.strip()[:80], "restored": b.strip()[:80]})
        else:
            print(f"⚠️ No live trades.csv to diff against — restored {result['restored_rows']} rows")
    finally:
        shutil.rmtree(str(tmpdir), ignore_errors=True)

    # Update data manifest
    _update_data_manifest("restore_drill_last_ok", _now_pt() if result["match"] else "FAIL")
    _update_data_manifest("restore_drill_last_rows", str(result["restored_rows"]))

    return result


# ── Prune ────────────────────────────────────────────────────────────────────

def prune_old_snapshots() -> int:
    """Remove snapshots older than RETENTION_DAYS."""
    cutoff = datetime.datetime.utcnow() - datetime.timedelta(days=RETENTION_DAYS)
    pruned = 0
    for snap in sorted(SNAPSHOT_DIR.glob("snapshot-*.d")):
        try:
            # Parse date from snapshot-YYYYMMDD.d
            date_str = snap.name.split("-")[1][:8]
            snap_date = datetime.datetime.strptime(date_str, "%Y%m%d")
            if snap_date.replace(tzinfo=datetime.timezone.utc) < cutoff.replace(tzinfo=datetime.timezone.utc):
                shutil.rmtree(snap)
                pruned += 1
                print(f"  Pruned: {snap.name}")
        except (ValueError, IndexError):
            pass
    return pruned


# ── Data Manifest Update ─────────────────────────────────────────────────────

def _update_data_manifest(key: str, value: str) -> None:
    """Update a single line in data-manifest.md."""
    if not DATA_MANIFEST_PATH.exists():
        return
    lines = DATA_MANIFEST_PATH.read_text().splitlines()
    with open(DATA_MANIFEST_PATH, "w") as f:
        updated = False
        for line in lines:
            if line.strip().startswith(f"{key}:"):
                f.write(f"{key}: {value}\n")
                updated = True
            else:
                f.write(line + "\n")
        if not updated:
            f.write(f"{key}: {value}\n")


# ── CLI ──────────────────────────────────────────────────────────────────────

def main():
    if "--snapshot" in sys.argv:
        print(f"=== Snapshot {_now_pt()} ===")
        result = create_snapshot()
        _update_data_manifest("snapshot_last_ok", _now_pt() if "error" not in result else f"FAIL: {result.get('error','')}")
        _update_data_manifest("snapshot_last_rows", str(result.get("journal_rows", 0)))
        _update_data_manifest("crosspost_state_bytes", str(result.get("crosspost_state_bytes", 0)))
        if result.get("offbox_copied"):
            _update_data_manifest("offbox_last_ok", _now_pt())

    elif "--restore-drill" in sys.argv:
        print(f"=== Restore Drill {_now_pt()} ===")
        result = run_restore_drill()
        if result.get("diffs"):
            for diff in result["diffs"][:5]:
                print(f"  Diff at line {diff['line']}: {diff['live'][:60]} != {diff['restored'][:60]}")

    elif "--prune" in sys.argv:
        print(f"=== Prune ({_now_pt()}) ===")
        pruned = prune_old_snapshots()
        print(f"  Pruned {pruned} old snapshots")

    elif "--manifest" in sys.argv:
        result = {
            "snapshot_last_ok": _now_pt(),
            "journal_rows": _manifest_record().get("journal_rows", "?"),
            "snapshots_on_disk": len(list(SNAPSHOT_DIR.glob("snapshot-*.d"))),
        }
        print(json.dumps(result, indent=2))

    else:
        print(__doc__)


if __name__ == "__main__":
    main()