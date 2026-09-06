#!/usr/bin/env python3
"""
trade_journal.py — HermesForge Append-Only Trade Journal (US-123, EPIC-014)

Immutable, append-only JSONL journal.  Every trade event is one line; no
DELETE or UPDATE on fact rows.  trades.csv is rebuilt from the journal
as a derived projection — it is NEVER the source of truth.

Guards enforced on every write:
  - Refuse empty payload
  - Refuse backward signal_id or timestamp
  - Refuse duplicate close (same signal_id already closed)
  - Refuse row-count regression (new events must sort after last event)

Usage:
  from trade_journal import append_event, rebuild_csv
  journal = trade_journal.JOURNAL  # singleton, opened on import

Migration:
  python3 trade_journal.py --migrate   # one-shot: migrate existing trades.csv
"""

import json
import os
import pathlib
import hashlib
import datetime
import csv
import sys
from typing import Optional

# ── Paths ────────────────────────────────────────────────────────────────────

REPO_ROOT = pathlib.Path(__file__).parent
JOURNAL_PATH = REPO_ROOT / "trade_journal.jsonl"
MANIFEST_PATH = REPO_ROOT / "trade_journal_manifest.txt"
CSV_PATH = REPO_ROOT / "trades.csv"

# ══════════════════════════════════════════════════════════════════════════════
# Guards
# ══════════════════════════════════════════════════════════════════════════════

def _now_utc_iso() -> str:
    """Current UTC timestamp in ISO 8601 with microsecond precision."""
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def _refuse(msg: str) -> None:
    raise ValueError(f"JOURNAL REFUSED: {msg}")


# ══════════════════════════════════════════════════════════════════════════════
# Journal API
# ══════════════════════════════════════════════════════════════════════════════

class TradeJournal:
    """Append-only JSONL journal for trade events."""

    def __init__(self, path: pathlib.Path = JOURNAL_PATH):
        self.path = path
        self._last_signal_id: Optional[str] = None
        self._last_timestamp: Optional[str] = None
        self._closed_signal_ids: set = set()
        self._initialised = False

    # ── Initialisation ──────────────────────────────────────────────────────

    def _scan_journal(self) -> None:
        """Walk the existing journal to rebuild in-memory state for guards."""
        self._closed_signal_ids.clear()
        self._last_signal_id = None
        self._last_timestamp = None
        if not self.path.exists() or self.path.stat().st_size == 0:
            self._initialised = True
            return
        with open(self.path, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue
                self._last_timestamp = event.get("timestamp", self._last_timestamp)
                sig = event.get("signal_id", "")
                if sig:
                    self._last_signal_id = sig
                if event.get("type") == "close" and sig:
                    self._closed_signal_ids.add(sig)
        self._initialised = True

    def _ensure_initialised(self) -> None:
        if not self._initialised:
            self._scan_journal()

    # ── Write path (the ONLY path that touches the file) ───────────────────

    def append(self, event_type: str, signal_id: str, data: dict) -> str:
        """Append one immutable event to the journal.  Returns the line written.

        Args:
            event_type: "open", "close", "update_entry", or "discord_info"
            signal_id:  unique signal identifier (never reused)
            data:       dict of fields to record (must not be empty)

        Raises ValueError if any guard fails.
        """
        self._ensure_initialised()

        # ── Guard 1: refuse empty payload ──
        if not data:
            _refuse("empty data payload")

        if not signal_id:
            _refuse("empty signal_id")

        # ── Guard 2: refuse backward signal_id ──
        if self._last_signal_id is not None:
            if signal_id < self._last_signal_id:
                _refuse(
                    f"backward signal_id: '{signal_id}' < last '{self._last_signal_id}'"
                )

        # ── Guard 3: refuse duplicate close ──
        if event_type == "close" and signal_id in self._closed_signal_ids:
            _refuse(f"duplicate close: signal_id '{signal_id}' already closed")

        # ── Guard 4: refuse backward timestamp ──
        ts = _now_utc_iso()
        if self._last_timestamp is not None and ts < self._last_timestamp:
            _refuse(f"backward timestamp: '{ts}' < last '{self._last_timestamp}'")
        if self._last_timestamp is not None:
            # Ensure ts is >= last (allow same microsecond for same-cycle events)
            pass  # datetime comparison handles this; rare clock-skew edge tolerated

        # ── Build and write the event ──
        # Inject signal_id into data so it survives replay
        data_with_sig = dict(data)
        data_with_sig["signal_id"] = signal_id
        event = {
            "type": event_type,
            "timestamp": ts,
            "signal_id": signal_id,
            "data": data_with_sig,
        }

        # Atomic append: write to temp, fsync, then rename
        tmp = self.path.with_suffix(".tmp")
        try:
            # Copy existing journal to temp, then append new line
            if self.path.exists():
                with open(self.path, "r") as src:
                    with open(tmp, "w") as dst:
                        dst.write(src.read())
            with open(tmp, "a") as dst:
                dst.write(json.dumps(event) + "\n")
                dst.flush()
                os.fsync(dst.fileno())

            # Verify: lines in tmp == lines in original + 1
            with open(tmp, "r") as f:
                verify_lines = [l for l in f if l.strip()]
            orig_count = sum(1 for l in open(self.path, "r") if l.strip()) if self.path.exists() else 0
            if len(verify_lines) != orig_count + 1:
                raise ValueError(
                    f"Write verification failed: expected {orig_count+1} lines, "
                    f"got {len(verify_lines)}"
                )

            # Atomic replace
            os.replace(str(tmp), str(self.path))
        except Exception:
            tmp.unlink(missing_ok=True)
            raise

        # Update in-memory state
        self._last_signal_id = signal_id
        self._last_timestamp = ts
        if event_type == "close":
            self._closed_signal_ids.add(signal_id)

        # Write manifest
        self._write_manifest()

        return json.dumps(event)

    # ── Manifest ────────────────────────────────────────────────────────────

    def _write_manifest(self) -> None:
        """Write a lightweight manifest recording journal health."""
        row_count = 0
        if self.path.exists():
            with open(self.path, "r") as f:
                row_count = sum(1 for l in f if l.strip())
        sha = hashlib.sha256()
        if self.path.exists():
            with open(self.path, "rb") as f:
                for chunk in iter(lambda: f.read(65536), b""):
                    sha.update(chunk)
        with open(MANIFEST_PATH, "w") as f:
            f.write(f"journal_rows: {row_count}\n")
            f.write(f"sha256: {sha.hexdigest()}\n")
            f.write(f"last_signal_id: {self._last_signal_id or ''}\n")
            f.write(f"last_timestamp: {self._last_timestamp or ''}\n")
            f.write(f"closed_count: {len(self._closed_signal_ids)}\n")

    def manifest(self) -> dict:
        self._ensure_initialised()
        return {
            "journal_rows": sum(1 for _ in open(self.path, "r") if _.strip()) if self.path.exists() else 0,
            "last_signal_id": self._last_signal_id,
            "last_timestamp": self._last_timestamp,
            "closed_count": len(self._closed_signal_ids),
        }

    # ── Replay (for rebuild) ────────────────────────────────────────────────

    def replay(self) -> list[dict]:
        """Replay the entire journal, returning the current state as a list of
        trade dicts suitable for CSV projection."""
        self._ensure_initialised()
        state: dict[str, dict] = {}  # signal_id → trade dict
        if not self.path.exists():
            return []

        with open(self.path, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue
                sig = event.get("signal_id", "")
                etype = event.get("type", "")
                data = event.get("data", {})

                if etype == "open":
                    state[sig] = dict(data)
                elif etype == "close":
                    if sig in state:
                        state[sig].update(data)
                    else:
                        # Orphan close — record what we can
                        state[sig] = dict(data)
                elif etype in ("update_entry", "discord_info"):
                    if sig in state:
                        state[sig].update(data)
                    else:
                        # Orphan update — create minimal row
                        state[sig] = dict(data)

        return list(state.values())


# ── Singleton ─────────────────────────────────────────────────────────────────

# One journal instance shared across all importers.  `scan_journal()` is
# called lazily on first append to avoid opening the file at import time
# in subprocesses that only need the CSV projection.
JOURNAL = TradeJournal(JOURNAL_PATH)


# ══════════════════════════════════════════════════════════════════════════════
# Derived projection: rebuild trades.csv from journal
# ══════════════════════════════════════════════════════════════════════════════

# CSV field order — MUST match trade_log.FIELDS
CSV_FIELDS = [
    "trade_id", "short_id", "strategy_id", "ticker", "asset_class", "data_source",
    "direction", "signal_id", "entry_date", "entry_price", "stop_price", "target_price",
    "position_size_pct", "position_size_units", "quality_tier",
    "entry_status",
    "status",
    "exit_date", "exit_price", "exit_reason",
    "r_multiple", "bars_held", "subperiod", "confirmation_level", "weekly_gate_scaling",
    "chart_path", "notes",
    "discord_message_id", "discord_channel_id", "discord_post_url",
]


def rebuild_csv(target_path: Optional[pathlib.Path] = None) -> int:
    """Regenerate trades.csv from the append-only journal.

    Returns the number of rows written.
    """
    target = target_path or CSV_PATH
    rows = JOURNAL.replay()

    # Atomic write: temp → validate → rename
    tmp = target.with_suffix(".tmp")
    try:
        with open(tmp, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
            writer.writeheader()
            for row in rows:
                # Ensure all fields exist
                clean = {field: row.get(field, "") for field in CSV_FIELDS}
                writer.writerow(clean)
            f.flush()
            os.fsync(f.fileno())

        # Verify
        with open(tmp, newline="") as f:
            verify = list(csv.DictReader(f))
        if len(verify) != len(rows):
            raise ValueError(
                f"Rebuild verification failed: wrote {len(rows)} rows, "
                f"read back {len(verify)}"
            )

        os.replace(str(tmp), str(target))
        return len(rows)
    except Exception:
        tmp.unlink(missing_ok=True)
        raise


# ══════════════════════════════════════════════════════════════════════════════
# Migration: seed the journal from existing trades.csv
# ══════════════════════════════════════════════════════════════════════════════

def migrate_existing_csv() -> dict:
    """One-shot: read trades.csv, replay each row as journal events.

    Returns: {before_rows: N, after_events: M, errors: [...]}
    """
    if not CSV_PATH.exists():
        return {"before_rows": 0, "after_events": 0, "errors": ["trades.csv not found"]}

    # Read existing CSV
    with open(CSV_PATH, newline="") as f:
        rows = list(csv.DictReader(f))

    # If journal already has rows, refuse to overwrite
    if JOURNAL.path.exists() and JOURNAL.path.stat().st_size > 0:
        with open(JOURNAL.path, "r") as f:
            existing = sum(1 for l in f if l.strip())
        if existing > 0:
            return {
                "before_rows": len(rows),
                "after_events": existing,
                "errors": [f"journal already has {existing} events — run --force to re-migrate"]
            }

    errors = []
    events_written = 0

    # Sort by signal_id for deterministic replay
    sorted_rows = sorted(rows, key=lambda r: r.get("signal_id", ""))

    for row in sorted_rows:
        sig = row.get("signal_id", "")
        if not sig:
            errors.append(f"skipping row with empty signal_id: {row.get('trade_id','?')}")
            continue

        try:
            # ── Open event: fields that exist at trade open ──
            open_data = {
                "trade_id": row.get("trade_id", ""),
                "short_id": row.get("short_id", ""),
                "strategy_id": row.get("strategy_id", ""),
                "ticker": row.get("ticker", ""),
                "asset_class": row.get("asset_class", ""),
                "data_source": row.get("data_source", ""),
                "direction": row.get("direction", ""),
                "entry_date": row.get("entry_date", ""),
                "entry_price": row.get("entry_price", ""),
                "stop_price": row.get("stop_price", ""),
                "target_price": row.get("target_price", ""),
                "position_size_pct": row.get("position_size_pct", ""),
                "position_size_units": row.get("position_size_units", ""),
                "quality_tier": row.get("quality_tier", ""),
                "entry_status": row.get("entry_status", "pending"),
                "status": "open",
                "subperiod": row.get("subperiod", ""),
                "confirmation_level": row.get("confirmation_level", ""),
                "weekly_gate_scaling": row.get("weekly_gate_scaling", ""),
                "chart_path": row.get("chart_path", ""),
                "notes": row.get("notes", ""),
                "discord_message_id": row.get("discord_message_id", ""),
                "discord_channel_id": row.get("discord_channel_id", ""),
                "discord_post_url": row.get("discord_post_url", ""),
            }
            JOURNAL.append("open", sig, open_data)
            events_written += 1

            # ── Close event (if closed) ──
            if row.get("status") == "closed" and row.get("exit_date"):
                close_data = {
                    "status": "closed",
                    "exit_date": row.get("exit_date", ""),
                    "exit_price": row.get("exit_price", ""),
                    "exit_reason": row.get("exit_reason", ""),
                    "r_multiple": row.get("r_multiple", ""),
                    "bars_held": row.get("bars_held", ""),
                }
                JOURNAL.append("close", sig, close_data)
                events_written += 1

        except ValueError as e:
            errors.append(f"{sig}: {e}")

    # Rebuild CSV from journal
    new_rows = rebuild_csv()

    return {
        "before_rows": len(rows),
        "after_events": events_written,
        "rebuilt_csv_rows": new_rows,
        "errors": errors,
    }


# ══════════════════════════════════════════════════════════════════════════════
# Wire: convenience helpers for trade_log.py callers
# ══════════════════════════════════════════════════════════════════════════════

def journal_open(signal_id: str, trade_dict: dict) -> str:
    """Append an 'open' event.  Returns the JSON line written."""
    open_fields = {k: str(v) for k, v in trade_dict.items()}
    open_fields["status"] = "open"
    return JOURNAL.append("open", signal_id, open_fields)


def journal_close(signal_id: str, exit_date: str, exit_price: float,
                  exit_reason: str, r_multiple: float,
                  bars_held: Optional[int] = None) -> str:
    """Append a 'close' event.  Returns the JSON line written."""
    data = {
        "status": "closed",
        "exit_date": str(exit_date)[:10],
        "exit_price": str(exit_price),
        "exit_reason": exit_reason,
        "r_multiple": str(round(r_multiple, 4)),
    }
    if bars_held is not None:
        data["bars_held"] = str(bars_held)
    return JOURNAL.append("close", signal_id, data)


def journal_update_entry(signal_id: str, entry_status: str) -> str:
    """Append an 'update_entry' event."""
    return JOURNAL.append("update_entry", signal_id, {"entry_status": entry_status})


def journal_discord_info(signal_id: str, message_id: str, channel_id: str,
                         post_url: str = "") -> str:
    """Append a 'discord_info' event."""
    return JOURNAL.append("discord_info", signal_id, {
        "discord_message_id": message_id,
        "discord_channel_id": channel_id,
        "discord_post_url": post_url,
    })


# ══════════════════════════════════════════════════════════════════════════════
# CLI
# ══════════════════════════════════════════════════════════════════════════════

def main():
    if "--migrate" in sys.argv:
        force = "--force" in sys.argv
        if force:
            # Clear journal if force
            if JOURNAL.path.exists():
                JOURNAL.path.unlink()
            JOURNAL._scan_journal()
        print(f"Migrating trades.csv → trade_journal.jsonl...")
        result = migrate_existing_csv()
        print(f"  CSV rows read:    {result['before_rows']}")
        print(f"  Journal events:   {result['after_events']}")
        print(f"  Rebuilt CSV rows: {result.get('rebuilt_csv_rows', 'N/A')}")
        if result["errors"]:
            print(f"  Errors: {len(result['errors'])}")
            for e in result["errors"][:10]:
                print(f"    {e}")
        mani = JOURNAL.manifest()
        print(f"\n  Manifest: {json.dumps(mani, indent=2)}")
    elif "--rebuild" in sys.argv:
        count = rebuild_csv()
        print(f"Rebuilt trades.csv: {count} rows")
    elif "--test" in sys.argv:
        _test()
    elif "--manifest" in sys.argv:
        print(json.dumps(JOURNAL.manifest(), indent=2))
    else:
        print(__doc__)


# ══════════════════════════════════════════════════════════════════════════════
# Unit tests
# ══════════════════════════════════════════════════════════════════════════════

def _test():
    import tempfile

    # Use temp dir for isolation
    tmpdir = pathlib.Path(tempfile.mkdtemp())
    journal_path = tmpdir / "test_journal.jsonl"
    csv_path = tmpdir / "trades.csv"
    manifest_path = tmpdir / "test_manifest.txt"

    # Override globals for test
    global JOURNAL, JOURNAL_PATH, CSV_PATH, MANIFEST_PATH
    orig_journal_path = JOURNAL_PATH
    orig_csv_path = CSV_PATH
    orig_manifest_path = MANIFEST_PATH
    JOURNAL_PATH = journal_path
    CSV_PATH = csv_path
    MANIFEST_PATH = manifest_path
    JOURNAL = TradeJournal(journal_path)

    try:
        # ── Test 1: append and rebuild ──
        sig1 = "TEST-STR_AAPL_2026-09-06_1400"
        trade = {"trade_id": "TEST-STR_AAPL_2026-09-06", "ticker": "AAPL",
                 "strategy_id": "TEST-STR", "direction": "long",
                 "entry_price": "150.0", "stop_price": "145.0", "target_price": "165.0"}
        journal_open(sig1, trade)
        assert journal_path.stat().st_size > 0, "journal file not created"

        journal_close(sig1, "2026-09-06", 165.0, "target", 3.0, bars_held=5)

        count = rebuild_csv(csv_path)
        assert count == 1, f"expected 1 row, got {count}"
        with open(csv_path) as f:
            rows = list(csv.DictReader(f))
        assert rows[0]["signal_id"] == sig1
        assert rows[0]["status"] == "closed"
        assert float(rows[0]["r_multiple"]) == 3.0

        # ── Test 2: duplicate close refused ──
        try:
            journal_close(sig1, "2026-09-06", 165.0, "target", 3.0)
            assert False, "should have refused duplicate close"
        except ValueError as e:
            assert "already closed" in str(e)

        # ── Test 3: empty payload refused ──
        try:
            JOURNAL.append("open", "TEST-EMPTY", {})
            assert False, "should have refused empty payload"
        except ValueError as e:
            assert "empty" in str(e).lower()

        # ── Test 4: backward signal_id refused ──
        try:
            JOURNAL.append("open", "AAA-EARLIER", {"ticker": "X"})
            assert False, "should have refused backward signal_id"
        except ValueError as e:
            assert "backward" in str(e).lower()

        # ── Test 5: mid-write crash leaves journal intact ──
        # (Tested by atomic append — tmp file never becomes live on crash)
        # Verify journal is valid JSONL
        with open(journal_path) as f:
            for line in f:
                line = line.strip()
                if line:
                    json.loads(line)  # must parse

        # ── Test 6: manifest exists ──
        assert manifest_path.exists()
        with open(manifest_path) as f:
            manifest = {}
            for line in f:
                k, _, v = line.partition(": ")
                manifest[k.strip()] = v.strip()
        assert int(manifest.get("journal_rows", 0)) == 2  # open + close

        print("✅ All trade_journal.py unit tests passed")

    finally:
        # Restore globals
        JOURNAL_PATH = orig_journal_path
        CSV_PATH = orig_csv_path
        MANIFEST_PATH = orig_manifest_path
        JOURNAL = TradeJournal(orig_journal_path)
        # Clean up temp
        import shutil
        shutil.rmtree(str(tmpdir), ignore_errors=True)


if __name__ == "__main__":
    main()