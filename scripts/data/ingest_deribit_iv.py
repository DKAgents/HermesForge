"""ingest_deribit_iv.py — HermesForge US-187: Deribit DVOL + ATM IV term structure.

Two cheap GET-based sub-feeds for BTC and ETH, one per hour:

  1. DVOL (vol-index level, %) via ``get_volatility_index_data`` (resolution
     = 3600, hourly candle) — the vol-of-vol LEVEL that gates the US-181 timing
     signal. First run backfills ~30d (Deribit bounds the reach).
  2. ATM IV term structure via ``get_instruments`` (option) joined on
     ``instrument_name`` with ``get_book_summary_by_currency`` (option), where
     ``mark_iv`` IS the IV surface in % (no Black-Scholes solve). Per expiry:
     ATM strike = nearest underlying_price; atm_iv = 0.5*(call+put mark_iv);
     dte = (expiration_timestamp - now)/86400000.

Both idempotent (PK dedup), skip-on-empty, never fabricate.

Usage:
    python3 ingest_deribit_iv.py [--dry-run] [--currency BTC ETH]
"""

from __future__ import annotations

import argparse
import sys
import time
import pathlib
from collections import defaultdict
from datetime import datetime, timezone

import requests

import iv_store

DERIBIT = "https://www.deribit.com/api/v2/public"

BACKFILL_DAYS = 30
SNAPSHOT_BUCKET_MS = 3600 * 1000   # hourly idempotency for crypto_atm_iv
MAX_RETRIES = 4
RETRY_BACKOFF_BASE = 2.0

CURRENCIES = ("BTC", "ETH")


def _now_ms() -> int:
    return int(time.time() * 1000)


def _get(path: str, params: dict) -> dict:
    """GET a Deribit public endpoint with 429/5xx backoff; raise on HTTP!=200."""
    last_err: Exception | None = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            resp = requests.get(f"{DERIBIT}{path}", params=params, timeout=30)
        except requests.RequestException as e:
            last_err = e
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_BACKOFF_BASE * (2 ** attempt))
                continue
            raise
        if resp.status_code in (429, 500, 502, 503, 504):
            last_err = RuntimeError(f"HTTP {resp.status_code}")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_BACKOFF_BASE * (2 ** attempt))
                continue
            resp.raise_for_status()
        resp.raise_for_status()
        return resp.json()
    if last_err is not None:
        raise last_err
    raise RuntimeError("_get: unreachable")


def fetch_dvol(currency: str, start_ms: int, end_ms: int) -> list[dict]:
    """DVOL candles -> [{ts, open, high, low, close}] ascending."""
    j = _get("/get_volatility_index_data", {
        "currency": currency, "resolution": "3600",
        "start_timestamp": int(start_ms), "end_timestamp": int(end_ms),
    })
    data = (j.get("result") or {}).get("data") or []
    rows = []
    for candle in data:
        try:
            ts, o, h, l, c = (int(candle[0]), float(candle[1]), float(candle[2]),
                              float(candle[3]), float(candle[4]))
        except (TypeError, ValueError, IndexError):
            continue
        rows.append({"currency": currency, "ts": ts, "open": o, "high": h,
                     "low": l, "close": c})
    return rows


def fetch_instruments(currency: str) -> list[dict]:
    j = _get("/get_instruments", {"currency": currency, "kind": "option",
                                  "expired": "false"})
    return j.get("result") or []


def fetch_book_summary(currency: str) -> list[dict]:
    j = _get("/get_book_summary_by_currency", {"currency": currency,
                                               "kind": "option"})
    return j.get("result") or []


def build_atm_term(currency: str, instruments: list[dict],
                   book_summary: list[dict], snap_ts: int) -> list[dict]:
    """Join instruments (strike/expiry/option_type) to book_summary (mark_iv/
    underlying_price) on instrument_name; emit one row per expiry at the ATM
    strike (nearest underlying_price), atm_iv = 0.5*(call+put mark_iv)."""
    bs = {b["instrument_name"]: b for b in book_summary}
    exp_map: dict[int, list] = defaultdict(list)
    ref_underlying: dict[int, float] = {}
    for inst in instruments:
        name = inst.get("instrument_name")
        b = bs.get(name)
        if b is None or b.get("mark_iv") is None:
            continue
        exp = inst.get("expiration_timestamp")
        if exp is None:
            continue
        try:
            iv = float(b["mark_iv"])
        except (TypeError, ValueError):
            continue
        exp_map[exp].append((inst.get("option_type"), inst.get("strike"),
                             iv))
        if (b.get("underlying_price") or 0) and exp not in ref_underlying:
            try:
                ref_underlying[exp] = float(b["underlying_price"])
            except (TypeError, ValueError):
                pass

    rows = []
    for exp, items in exp_map.items():
        under = ref_underlying.get(exp)
        if not under or under <= 0:
            continue
        strikes: dict[float, dict] = {}
        for otype, strike, iv in items:
            if strike is None:
                continue
            strikes.setdefault(strike, {})[otype] = iv
        if not strikes:
            continue
        atm_strike = min(strikes.keys(), key=lambda s: abs(s - under))
        pair = strikes[atm_strike]
        c_iv, p_iv = pair.get("call"), pair.get("put")
        if c_iv is None or p_iv is None:
            continue
        atm_iv = 0.5 * (c_iv + p_iv)
        dte = (exp - snap_ts) / 86400000.0
        rows.append({"currency": currency, "ts": snap_ts, "expiry": int(exp),
                     "dte": round(dte, 6), "atm_iv": atm_iv, "spot": under})
    return rows


def ingest_currency(conn, currency: str, dry_run: bool) -> dict:
    now = _now_ms()

    # ── DVOL (vol-index candle) ────────────────────────────────────────────
    dvol_last = iv_store.last_ts(conn, "dvol", currency)
    if dvol_last is None:
        dvol_start = now - BACKFILL_DAYS * 24 * 3600 * 1000
    else:
        dvol_start = dvol_last
    dvol_rows = fetch_dvol(currency, dvol_start, now)

    # ── ATM IV term structure ──────────────────────────────────────────────
    snap_ts = (now // SNAPSHOT_BUCKET_MS) * SNAPSHOT_BUCKET_MS
    atm_rows = build_atm_term(currency, fetch_instruments(currency),
                              fetch_book_summary(currency), snap_ts)

    if dry_run:
        return {"currency": currency, "ok": True, "dvol": len(dvol_rows),
                "atm": len(atm_rows), "dry_run": True}

    new_dvol = iv_store.append_dvol(conn, dvol_rows)
    new_atm = iv_store.append_crypto_atm_iv(conn, atm_rows)
    iso = datetime.now(timezone.utc).isoformat()
    if dvol_rows:
        iv_store.upsert_state(conn, "dvol", currency, max(r["ts"] for r in dvol_rows), iso)
    if atm_rows:
        iv_store.upsert_state(conn, "crypto_atm", currency, snap_ts, iso)
    return {"currency": currency, "ok": True, "new_dvol": new_dvol,
            "new_atm": new_atm, "dvol_rows": len(dvol_rows),
            "atm_rows": len(atm_rows)}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Ingest Deribit DVOL + ATM IV term structure into iv_store.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--currency", nargs="*", default=list(CURRENCIES))
    args = parser.parse_args()

    mode = "DRY-RUN" if args.dry_run else "INGEST"
    for currency in args.currency:
        try:
            conn = iv_store.open_store()
            try:
                res = ingest_currency(conn, currency, dry_run=args.dry_run)
            finally:
                conn.close()
        except Exception as e:
            print(f"[{mode}] {currency} FAILED: {e}")
            return 1
        if args.dry_run:
            print(f"[{mode}] {currency}: dvol={res['dvol']}, atm={res['atm']}")
        else:
            print(f"[{mode}] {currency}: new_dvol={res['new_dvol']}, "
                  f"new_atm={res['new_atm']} (dvol_rows={res['dvol_rows']}, "
                  f"atm_rows={res['atm_rows']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())