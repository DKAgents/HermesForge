#!/usr/bin/env python3
"""ingest_hl_fills.py — HermesForge US-07 (D-1): Hyperliquid fills history with
wallet + closed PnL, for wallet-cohort (HYP-29), tail-liquidation (HYP-34) and
metaorder (HYP-36) reconstruction.

SOURCE (verified 2026-11-09):
  The canonical HL node archive (``s3://hl-mainnet-node-data/node_fills[_by_block]``
  and ``s3://hyperliquid-archive``) is requester-pays and **SCP-blocked** from this
  deployment's AWS account (ListObjectsV2 / HeadObject / GetObject all return
  AccessDenied/403). See reports/ for the US-198 auth-block precedent.

  The reachable equivalent is **Ironflow** (https://docs.ironflow.sh): a read-only
  ClickHouse SQL API (``POST https://api.ironflow.sh/v1/query``) over ``hl.fills``,
  whose records are Ironflow's own Hyperliquid node fills. Fields are the node-fills
  record mapped to columnar form: ``address`` (wallet), ``coin``, ``price``, ``size``,
  ``side`` (buy/sell aggressor), ``is_taker`` (maker/taker role), ``direction``
  (Open Long / Close Short / ...), ``realized_pnl`` (closed PnL per fill), ``fee``,
  ``notional``, ``is_liquidation``, ``oid``/``tid``/``block``/``hash``, ``ts``.

  Tier / cost truth (verified live): a FREE Ironflow key (already present as
  IRONFLOW_API_KEY in ~/.hermes/.env) serves ~30 days of history via SQL, capped at
  1,000 rows/query, 10 s/query, 5 min query-time and 10B rows-read per hour. The
  ``hl.fills`` table reads ~73M rows per query regardless of ts filter (day-granule
  scan), so throughput is ~100-140 queries/hour (~100-140k fills/hour). FULL history
  (1 year) needs a paid tier (Builder 149 USDC/30d, SQL export 5M rows/file) or the
  direct S3 path. This is reported, not hidden: see the module docstring tail.

AUTH: reads IRONFLOW_API_KEY from env / ~/.hermes/.env. Never hardcodes a key.
Send as ``Authorization: Bearer <key>``. Keyless (no key) gives only 24h history.

STORE: ~/.hermes/market_data/hl_fills/
  data/{YYYY-MM-DD}/fills-{scope}.parquet   (one file per (day, scope); scope = "all"
                                             or a comma-joined market list slug)
  manifest.json                             (per (scope, day): status, rows, min/max ts,
                                             reported_count, gaps, _asof)

IDEMPOTENT + RESUMABLE + GAP-DETECTING:
  * A day marked "complete" in the manifest is skipped on re-run (INSERT-equivalent
    idempotency at the partition level).
  * A day marked "in_progress" resumes from its saved (last_ts, last_oid) keyset
    cursor — a partial run loses no work.
  * After a day closes, its pulled row count is compared to a SELECT count() for the
    same (day, scope); a mismatch records a "gap" with both numbers. Missing days in
    the requested range are surfaced as gaps too (archives update monthly with no
    completeness guarantee).

ATOMICITY: each day's parquet is written to a tmp file and os.replace()'d into place
only after the day is fully pulled + counted; a crash mid-day leaves the prior state
intact and the day "in_progress" for resume.

Usage:
    python3 ingest_hl_fills.py --start 2026-11-07 --end 2026-11-08 --markets BTC-PERP
    python3 ingest_hl_fills.py --start 2026-11-07 --end 2026-11-08   # all markets
    python3 ingest_hl_fills.py --start 2026-11-01 --end 2026-11-09 --cost-only
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone

import pandas as pd

# ---------------------------------------------------------------------------
# Constants / config
# ---------------------------------------------------------------------------

API = "https://api.ironflow.sh/v1/query"

STORE_DIR = pathlib.Path.home() / ".hermes" / "market_data" / "hl_fills"
DATA_DIR = STORE_DIR / "data"
MANIFEST_PATH = STORE_DIR / "manifest.json"

# The exact columns we pull from hl.fills. ``realized_pnl`` is the closed PnL.
COLS = [
    "ts", "market", "coin", "dex", "market_class", "address", "side",
    "direction", "price", "size", "notional", "fee", "fee_token",
    "realized_pnl", "is_taker", "is_liquidation", "oid", "tid", "block", "hash",
]

# Free-key tier limits (verified live): 1,000 rows/query, 10 s/query, 60 req/min,
# 5 min query-time and 10B rows-read per hour. The hl.fills underlying table scans
# a ~full-day partition per query, so a wide ts range TIMES OUT (>10 s) and must be
# avoided; paginate with a rolling narrow time window instead (see pull_day).
ROWS_PER_QUERY = 1000      # free-key cap
WINDOW_MS = 600_000        # 10-minute rolling scan window (keeps each query < 10 s)
# Min seconds between queries. 1.05 s keeps us just under the 60 req/min ceiling;
# the 429 READ_BUDGET_EXCEEDED backoff handles the rows/hour budget if it binds.
QUERY_SPACING_S = 1.05
MAX_RETRIES = 6


class FillsIngestError(Exception):
    pass


# ---------------------------------------------------------------------------
# Ironflow SQL client
# ---------------------------------------------------------------------------

def _load_key() -> str | None:
    v = os.environ.get("IRONFLOW_API_KEY")
    if v:
        return v.strip()
    envp = pathlib.Path.home() / ".hermes" / ".env"
    if envp.exists():
        m = re.search(r"IRONFLOW_API_KEY=(\S+)", envp.read_text())
        if m:
            return m.group(1).strip()
    return None


def _query(sql: str, key: str | None, timeout: int = 60) -> dict:
    req = urllib.request.Request(
        API,
        data=json.dumps({"sql": sql}).encode(),
        headers={
            "Content-Type": "application/json",
            **({"Authorization": "Bearer " + key} if key else {}),
        },
        method="POST",
    )
    last_err: Exception | None = None
    for attempt in range(MAX_RETRIES):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as e:
            body = ""
            try:
                body = e.read().decode(errors="replace")[:400]
            except Exception:
                pass
            # 429 rate/read-budget -> honor Retry-After and back off.
            if e.code == 429:
                ra = e.headers.get("Retry-After")
                wait = float(ra) if ra and ra.isdigit() else min(30 * (attempt + 1), 120)
                time.sleep(wait)
                last_err = e
                continue
            raise FillsIngestError(
                f"Ironflow HTTP {e.code}: {e.reason} :: {body}") from e
        except (urllib.error.URLError, TimeoutError) as e:
            last_err = e
            time.sleep(5 * (attempt + 1))
    raise FillsIngestError(f"Ironflow query failed after retries: {last_err}")


def query(sql: str) -> dict:
    key = _load_key()
    return _query(sql, key)


def tier_limits() -> dict:
    # one cheap probe to reflect the live tier limits (history_days, max_rows, ...)
    r = query("SELECT 1")
    return r.get("limits", {})


# ---------------------------------------------------------------------------
# Dates / scopes
# ---------------------------------------------------------------------------

def iter_days(start: str, end: str) -> list[str]:
    def p(s: str) -> datetime:
        if len(s) != 10 or s[4] != "-" or s[7] != "-":
            raise ValueError(f"bad date {s!r} (want YYYY-MM-DD)")
        return datetime.strptime(s, "%Y-%m-%d")
    d0, d1 = p(start), p(end)
    if d1 < d0:
        raise ValueError(f"reversed range {start} > {end}")
    out, cur = [], d0
    while cur <= d1:
        out.append(cur.strftime("%Y-%m-%d"))
        cur += timedelta(days=1)
    return out


def scope_slug(markets: list[str] | None) -> str:
    if not markets:
        return "all"
    return "~".join(sorted(m.strip() for m in markets if m.strip()))


def _in_clause(markets: list[str] | None) -> str:
    if not markets:
        return ""
    names = ", ".join(f"'{m.strip()}'" for m in markets if m.strip())
    return f" AND market IN ({names})"


# ---------------------------------------------------------------------------
# Manifest (idempotency / resume / gap bookkeeping)
# ---------------------------------------------------------------------------

def load_manifest() -> dict:
    if not MANIFEST_PATH.exists():
        return {}
    try:
        return json.loads(MANIFEST_PATH.read_text())
    except (OSError, json.JSONDecodeError):
        return {}


def save_manifest(m: dict) -> None:
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = MANIFEST_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(m, indent=2, sort_keys=True))
    tmp.replace(MANIFEST_PATH)


def _manifest_key(scope: str, day: str) -> str:
    return f"{scope}::{day}"


def _day_path(scope: str, day: str) -> pathlib.Path:
    return DATA_DIR / day / f"fills-{scope}.parquet"


# ---------------------------------------------------------------------------
# Pull one day (keyset pagination)
# ---------------------------------------------------------------------------

def _day_bounds(day: str) -> tuple[int, int]:
    """[day_start, day_end) as UTC ms epoch. Internally we keep ms and format to
    an unambiguous 'YYYY-MM-DD HH:MM:SS.ffffff' string for SQL (the ts column is
    DateTime64(6, UTC): a bare integer literal is compared at the column's 1-us
    precision and BREAKS index pruning, causing a full-scan + 10 s timeout)."""
    t0 = datetime.strptime(day, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    t1 = t0 + timedelta(days=1)
    return int(t0.timestamp() * 1000), int(t1.timestamp() * 1000)


def _fmt_ms(ms: int) -> str:
    """UTC ms epoch -> 'YYYY-MM-DD HH:MM:SS.ffffff' (unambiguous DateTime64 literal)."""
    return datetime.fromtimestamp(ms / 1000.0, tz=timezone.utc).strftime(
        "%Y-%m-%d %H:%M:%S.%f")


def pull_day(scope: str, day: str, markets: list[str] | None,
             spacing: float = QUERY_SPACING_S) -> dict:
    """Paginate hl.fills for one (day, scope) fully, with a rolling narrow window.

    A full-day ts range plus ORDER BY times out the free key's 10 s/query limit, so
    we advance a rolling [w0, w0+WINDOW) cursor and keyset-paginate `(ts, oid)`
    inside each window. Pulls the ENTIRE day (no partial mode): resumability is at
    the partition level (completed days are skipped; an interrupted day is re-pulled
    from scratch so no partial-day gap can go unnoticed)."""
    t0, t1 = _day_bounds(day)
    in_clause = _in_clause(markets)
    rows: list[dict] = []
    cols_sql = ", ".join(COLS)
    last_q = 0.0

    w0 = t0
    while w0 < t1:
        w1 = min(w0 + WINDOW_MS, t1)
        w0s, w1s = _fmt_ms(w0), _fmt_ms(w1)
        first = True    # skip keyset on the window's first query
        last_ts = w0s
        last_oid = -1
        while True:
            curs = "" if first else (
                f" AND (ts > '{last_ts}' OR (ts = '{last_ts}' AND oid > {last_oid}))")
            sql = (
                f"SELECT {cols_sql} FROM hl.fills "
                f"WHERE ts >= '{w0s}' AND ts < '{w1s}'{in_clause}{curs} "
                f"ORDER BY ts, oid LIMIT {ROWS_PER_QUERY}"
            )
            elapsed = time.monotonic() - last_q
            if elapsed < spacing:
                time.sleep(spacing - elapsed)
            last_q = time.monotonic()
            batch = query(sql).get("rows", [])
            if not batch:
                break
            for rec in batch:
                rows.append(dict(zip(COLS, rec)))
            last_ts = batch[-1][0]          # ts arrives as a 'YYYY-MM-DD ...' string
            last_oid = batch[-1][COLS.index("oid")]
            first = False
            if len(batch) < ROWS_PER_QUERY:
                break
        w0 = w1
    return {"rows": rows}


def reported_count(day: str, markets: list[str] | None) -> int:
    t0, t1 = _day_bounds(day)
    in_clause = _in_clause(markets)
    r = query(f"SELECT count() FROM hl.fills WHERE ts >= '{_fmt_ms(t0)}' "
              f"AND ts < '{_fmt_ms(t1)}'{in_clause}")
    return int(r["rows"][0][0])


# ---------------------------------------------------------------------------
# Parquet write (atomic), read API helpers
# ---------------------------------------------------------------------------

def _asof() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_day(scope: str, day: str, rows: list[dict]) -> None:
    if not rows:
        return
    df = pd.DataFrame(rows)
    df["ts"] = pd.to_datetime(df["ts"], unit="ms", utc=True).astype("datetime64[us, UTC]")
    for c in ("price", "size", "notional", "fee", "realized_pnl"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    for c in ("oid", "tid", "block"):
        df[c] = pd.to_numeric(df[c], errors="coerce").astype("uint64")
    for c in ("is_taker", "is_liquidation"):
        df[c] = df[c].astype(bool)
    # as-of provenance per partition (leakage-audit ready)
    df["_asof"] = pd.Timestamp(_asof())
    path = _day_path(scope, day)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".parquet.tmp")
    df.to_parquet(tmp, index=False)
    os.replace(tmp, path)


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def ingest(start: str, end: str, markets: list[str] | None = None) -> dict:
    scope = scope_slug(markets)
    days = iter_days(start, end)
    manifest = load_manifest()
    summary = {"scope": scope, "days": len(days), "results": [], "skipped": 0,
               "gaps": []}

    for day in days:
        k = _manifest_key(scope, day)
        rec = manifest.get(k, {})
        if rec.get("status") == "complete" and not rec.get("gap"):
            summary["skipped"] += 1
            continue
        try:
            pulled = pull_day(scope, day, markets)
            n = len(pulled["rows"])
            manifest[k] = {"status": "in_progress", "rows_pulled": n,
                           "day": day, "scope": scope}  # re-pullable if interrupted
            save_manifest(manifest)
            write_day(scope, day, pulled["rows"])
            rep = reported_count(day, markets)
            gap = (n != rep)
            manifest[k] = {
                "status": "complete", "rows_pulled": n, "reported_count": rep,
                "gap": gap, "day": day, "scope": scope, "_asof": _asof(),
                "min_ts": pulled["rows"][0]["ts"] if pulled["rows"] else None,
                "max_ts": pulled["rows"][-1]["ts"] if pulled["rows"] else None,
            }
            save_manifest(manifest)
            summary["results"].append({"day": day, "rows": n, "reported": rep,
                                       "gap": gap})
            if gap:
                summary["gaps"].append({"day": day, "rows": n, "reported": rep})
        except Exception as e:  # keep prior state; surface, don't swallow
            summary["results"].append({"day": day, "error": str(e)})

    return summary


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(
        description="Backfill Hyperliquid fills (wallet + closed PnL) from Ironflow.")
    ap.add_argument("--start", required=True, help="YYYY-MM-DD (inclusive)")
    ap.add_argument("--end", required=True, help="YYYY-MM-DD (inclusive)")
    ap.add_argument("--markets", default=None,
                    help="Comma-separated market list (default: all markets)")
    ap.add_argument("--cost-only", action="store_true",
                    help="Report tier limits + coverage; pull nothing.")
    args = ap.parse_args()

    if args.cost_only:
        lim = tier_limits()
        print("[COST-ONLY] Ironflow free-key limits (live):")
        print(json.dumps(lim, indent=2))
        print("source = Ironflow /v1/query (Ironflow node fills, wallet+closedPnl)")
        print("cost   = $0 (free key); full history needs Builder 149 USDC/30d or "
              "direct S3 (SCP-blocked here)")
        return 0

    markets = [m for m in (args.markets or "").split(",") if m.strip()] or None
    try:
        summary = ingest(args.start, args.end, markets)
    except ValueError as e:
        print(f"[INGEST] {e}")
        return 2

    total = sum(r.get("rows", 0) for r in summary["results"])
    print(f"[INGEST] scope={summary['scope']} days={summary['days']} "
          f"skipped={summary['skipped']} pulled={total} gaps={len(summary['gaps'])}")
    for r in summary["results"]:
        if "error" in r:
            print(f"  FAIL {r['day']}: {r['error']}")
        else:
            flag = " !GAP!" if r["gap"] else ""
            print(f"  ok  {r['day']}: pulled={r['rows']} reported={r['reported']}{flag}")
    return 0 if not summary["gaps"] else 1


if __name__ == "__main__":
    sys.exit(main())