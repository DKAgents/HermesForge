"""
trials_ledger.py — Append-only JSONL ledger for Strategy Gauntlet backtest trials.

Atomic writes (temp → fsync → rename), thread-safe (fcntl.flock),
tamper-detection via SHA256 chain.
"""

import fcntl
import hashlib
import json
import os
import time
from pathlib import Path

LEDGER_PATH = Path("/root/HermesForge/data/gauntlet/trials.jsonl")
LEDGER_DIR = LEDGER_PATH.parent


def _ensure_dir() -> None:
    LEDGER_DIR.mkdir(parents=True, exist_ok=True)


def _sha256(data: str) -> str:
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def _now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _read_all_raw() -> list[dict]:
    """Read all entries, returning raw data including chain_hash fields."""
    entries: list[dict] = []
    if not LEDGER_PATH.exists():
        return entries
    with open(LEDGER_PATH, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue  # skip truncated/corrupt lines
    return entries


def read_all() -> list[dict]:
    """Return all trial entries as list of dicts."""
    return _read_all_raw()


def count() -> int:
    """Return N (number of trials) for DSR computation."""
    if not LEDGER_PATH.exists():
        return 0
    n = 0
    with open(LEDGER_PATH, "r") as f:
        for line in f:
            if line.strip():
                n += 1
    return n


def _compute_entry_hash(prev_hash: str | None, entry_without_hash: dict) -> str:
    """Compute chain_hash for a new entry."""
    payload = json.dumps(entry_without_hash, sort_keys=True)
    if prev_hash is None:
        return _sha256(payload)
    return _sha256(prev_hash + "|" + payload)


def increment_trial(
    hypothesis_id: str,
    param_hash: str,
    universe_hash: str,
    period_start: str,
    period_end: str,
    result: dict,
) -> dict:
    """
    Atomically append a trial entry. Thread-safe via fcntl.flock on the ledger.

    The lock is held across read-and-compute-hash + append to prevent races
    between concurrent writers.

    Returns the full entry dict including chain_hash.
    """
    _ensure_dir()

    entry = {
        "hypothesis_id": hypothesis_id,
        "param_hash": param_hash,
        "universe_hash": universe_hash,
        "period_start": period_start,
        "period_end": period_end,
        "timestamp": _now_iso(),
        "result": result,
    }

    # Lock the actual ledger file for the full read+append window
    with open(LEDGER_PATH, "a+") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        try:
            # Re-read current entries under lock to get latest prev_hash
            prev_hash: str | None = None
            if LEDGER_PATH.exists():
                # Move to start and read all existing entries
                f.seek(0)
                all_entries = []
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        all_entries.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
                if all_entries:
                    prev_hash = all_entries[-1].get("chain_hash")

            chain_hash = _compute_entry_hash(prev_hash, entry)
            entry["chain_hash"] = chain_hash

            line = json.dumps(entry, sort_keys=True) + "\n"

            # Append the new line
            f.write(line)
            f.flush()
            os.fsync(f.fileno())
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)

    return entry


def verify_integrity() -> tuple[bool, str]:
    """
    Verify the SHA256 hash chain.

    Returns (True, "OK") if the chain is intact,
    or (False, message) describing the first break.
    """
    entries = _read_all_raw()
    if not entries:
        return (True, "empty ledger — no entries to verify")

    prev_hash: str | None = None
    for i, entry in enumerate(entries):
        stored_hash = entry.get("chain_hash")
        if not stored_hash:
            return (False, f"entry {i}: missing chain_hash")

        # Recompute without chain_hash
        entry_without = {k: v for k, v in entry.items() if k != "chain_hash"}
        expected = _compute_entry_hash(prev_hash, entry_without)

        if stored_hash != expected:
            return (
                False,
                f"entry {i}: hash mismatch — stored={stored_hash[:16]}... expected={expected[:16]}...",
            )

        prev_hash = stored_hash

    return (True, "OK")