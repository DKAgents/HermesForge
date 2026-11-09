#!/usr/bin/env python3
"""
fill_telemetry.py — Hyperliquid live-fill telemetry (M-10, feeds G3).

Logs every LIVE order's execution outcome so the G3 fill-realism model
(execution_sim / fill-mode dispatch) can be recalibrated MONTHLY from real
fills instead of the current calibrated guesses. This is the data path for the
future $100 live micro-test.

Per-order record (append-only JSONL, one object/line):
  - venue            (always "hyperliquid")
  - instrument       ("perp" | "spot")
  - coin, side       ("buy" | "sell")
  - order_type       ("maker" | "taker" | "trigger_stop")
  - filled           (bool — includes no-fill outcomes, they are data too)
  - queue_position   (book-queue position at rest, if the venue reports it)
  - time_to_fill_ms  (order submit -> fill; null for no-fill)
  - markouts         (1m / 5m / 1h signed price drift from fill, favorable-positive)
  - fees             (bps + usd actually charged)

Markout convention (the adverse-selection measure G3 needs): signed future drift
in the direction of the trade's P&L, so NEGATIVE = adverse selection.
    buy  -> markout_bps = (px_future - fill_price) / fill_price * 1e4
    sell -> markout_bps = (fill_price - px_future) / fill_price * 1e4

SCOPE (M-10): this module is the LOGGER + READ PATH only. It does NOT place
orders and does NOT wire into live execution — that is the separately-approved
[APPROVAL] step. LIVE stays OFF. It is importable by future execution code and
by the G3 recalibration reader with zero network side effects.

Usage:
    from fill_telemetry import record_fill, read_fills, g3_recalibration_input
    record_fill({"venue": "hyperliquid", "instrument": "perp", "coin": "ETH",
                 "side": "sell", "order_type": "maker", "filled": True, ...})
    fills = read_fills(since_ms=...)
    cal = g3_recalibration_input()   # monthly recalibration feed for G3
"""

from __future__ import annotations

import json
import os
import fcntl
import time
import pathlib
from datetime import datetime, timezone
from typing import Optional

LOG_PATH = pathlib.Path(os.environ.get(
    "FILL_TELEMETRY_LOG",
    str(pathlib.Path(__file__).resolve().parent / "fill_telemetry.jsonl"),
))

SCHEMA_VERSION = "fill_telemetry_v1"

# Fields REQUIRED on every record. Missing one -> refuse (fail-closed): a
# malformed telemetry row is worse than a missing row (it would silently poison
# the G3 recalibration — same principle as the fee-source fail-closed anchor).
REQUIRED_FIELDS = ("venue", "instrument", "coin", "side", "order_type", "filled")

# Fields whose presence is optional (no-fill orders have no fill price/ttf; a
# record may be written before markouts are observed).
OPTIONAL_FIELDS = (
    "queue_position", "time_to_fill_ms", "fill_price", "fill_size",
    "size_usd", "fees_bps", "fees_usd", "mark_price_at_fill",
    "markout_1m_bps", "markout_5m_bps", "markout_1h_bps",
    "order_id", "strategy_id", "trade_id",
)

_VALID_ORDER_TYPES = ("maker", "taker", "trigger_stop")
_VALID_SIDES = ("buy", "sell")
_VALID_INSTRUMENTS = ("perp", "spot")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _validate(fill: dict) -> None:
    """Fail-closed schema validation. Raises ValueError on any violation."""
    if not isinstance(fill, dict):
        raise ValueError("fill record must be a dict")
    for k in REQUIRED_FIELDS:
        if k not in fill or fill[k] in (None, ""):
            raise ValueError(f"missing required field: {k!r}")
    if fill["side"] not in _VALID_SIDES:
        raise ValueError(f"unknown side={fill['side']!r}")
    if fill["order_type"] not in _VALID_ORDER_TYPES:
        raise ValueError(f"unknown order_type={fill['order_type']!r}")
    if fill["instrument"] not in _VALID_INSTRUMENTS:
        raise ValueError(f"unknown instrument={fill['instrument']!r}")
    if not isinstance(fill["filled"], bool):
        raise ValueError("filled must be a bool")
    if fill.get("time_to_fill_ms") is not None and fill["time_to_fill_ms"] < 0:
        raise ValueError("time_to_fill_ms must be >= 0")


def _canonicalize(fill: dict) -> dict:
    """Return a schema-pinned dict (only known fields), with ts stamped."""
    ts_iso = fill.get("ts") or _now_iso()
    if "ts_ms" in fill and fill["ts_ms"] is not None:
        ts_ms = float(fill["ts_ms"])
    else:
        try:
            dt = datetime.fromisoformat(str(ts_iso).replace("Z", "+00:00"))
            ts_ms = dt.timestamp() * 1000
        except (ValueError, TypeError):
            ts_ms = time.time() * 1000
    out = {
        "schema": SCHEMA_VERSION,
        "ts": ts_iso,
        "ts_ms": ts_ms,
    }
    for k in REQUIRED_FIELDS:
        out[k] = fill[k]
    for k in OPTIONAL_FIELDS:
        if k in fill:
            out[k] = fill[k]
    # Always-present extras (strategy/trade id default empty rather than absent).
    out.setdefault("strategy_id", None)
    out.setdefault("trade_id", None)
    return out


def _append_jsonl(obj: dict) -> None:
    """Append one JSONL object with an advisory lock (single-writer safe)."""
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(obj, sort_keys=True) + "\n"
    with open(LOG_PATH, "a") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        try:
            f.write(line)
            f.flush()
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)


def record_fill(fill: dict) -> dict:
    """Validate, canonicalize, and append ONE fill/order record. Returns the
    recorded object (with schema + ts). Raises ValueError on a bad record."""
    _validate(fill)
    rec = _canonicalize(fill)
    _append_jsonl(rec)
    return rec


def _read_all() -> list[dict]:
    if not LOG_PATH.exists():
        return []
    out = []
    with open(LOG_PATH) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return out


def read_fills(since_ms: Optional[int] = None) -> list[dict]:
    """READ PATH. Return all records (optionally only those with ts >= since_ms).

    `since_ms` is epoch milliseconds; records are matched on a stored
    `ts_ms` epoch if present, else parsed from the ISO `ts` field.
    """
    rows = _read_all()
    if since_ms is None:
        return rows
    out = []
    for r in rows:
        ts = r.get("ts_ms")
        if ts is None:
            iso = r.get("ts")
            if iso:
                try:
                    dt = datetime.fromisoformat(str(iso).replace("Z", "+00:00"))
                    ts = int(dt.timestamp() * 1000)
                except (ValueError, TypeError):
                    ts = None
        if ts is None or ts >= since_ms:
            out.append(r)
    return out


def g3_recalibration_input(since_ms: Optional[int] = None) -> dict:
    """Aggregate the telemetry into the summary the G3 fill model consumes.

    Returns (over the selected window):
      - n_records, n_fills, fill_rate  (maker fill probability calibration)
      - maker_ratio                    (share of fills that were maker orders)
      - time_to_fill_ms: mean/median/p90
      - markouts: mean/median 1m/5m/1h signed bps (adverse-selection estimate;
        a NEGATIVE mean markout = adverse selection on fills)
    """
    rows = read_fills(since_ms)
    filled = [r for r in rows if r.get("filled") is True]

    def _f(v):
        try:
            return float(v)
        except (TypeError, ValueError):
            return None

    def _stat(vals):
        vals = [v for v in vals if v is not None]
        if not vals:
            return {"n": 0}
        s = sorted(vals)
        n = len(s)
        return {
            "n": n,
            "mean": sum(s) / n,
            "median": s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2,
            "p90": s[min(n - 1, int(n * 0.9))],
        }

    ttf = [_f(r.get("time_to_fill_ms")) for r in filled]
    mark1 = [_f(r.get("markout_1m_bps")) for r in filled]
    mark5 = [_f(r.get("markout_5m_bps")) for r in filled]
    mark1h = [_f(r.get("markout_1h_bps")) for r in filled]

    maker_fills = [r for r in filled if r.get("order_type") == "maker"]

    return {
        "n_records": len(rows),
        "n_fills": len(filled),
        "fill_rate": (len(filled) / len(rows)) if rows else None,
        "maker_ratio": (len(maker_fills) / len(filled)) if filled else None,
        "time_to_fill_ms": _stat(ttf),
        "markout_1m_bps": _stat(mark1),
        "markout_5m_bps": _stat(mark5),
        "markout_1h_bps": _stat(mark1h),
    }


if __name__ == "__main__":
    cal = g3_recalibration_input()
    print(json.dumps(cal, indent=2, default=str))