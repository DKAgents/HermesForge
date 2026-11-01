"""ingest_hl_funding.py — HermesForge US-179: Hyperliquid funding ingestion.

Incrementally ingests HOURLY funding-rate + premium history into the persistent
SQLite funding store (~/.hermes/market_data/hl_funding/), closing the exact gap
where fetch_hyperliquid_metrics.py's parquet cache is TTL-OVERWRITTEN (only a
rolling window) and therefore cannot serve a deep carry backtest.

Design (per architect_us179_180_spec.md §1.1.2, mirroring US-177 ingest_hl_bars):
  * Universe from hermes_config.universe CRYPTO_UNIVERSE (single source of truth).
  * ``fundingHistory`` returns HOURLY rates, capped at 500 entries/call, ascending
    from ``startTime``. PAGINATION = walk forward (next startTime = last `time`
    +1ms) — ``endTime`` is NOT relied on for pagination (F4).
  * Incremental + idempotent: high-water-mark window with a 2h overlap; append via
    INSERT OR IGNORE dedups re-fetched overlaps to zero new rows.
  * First run seeds ~400 days (deep retention confirmed by live probe).
  * State mutated only AFTER a fully-successful append (never partial).

Usage:
    python3 ingest_hl_funding.py [--dry-run] [--coins BTC ETH ...]
"""

from __future__ import annotations

import argparse
import sys
import time
import pathlib
from datetime import datetime, timezone

import requests

import hl_funding_store

# Universe (single source of truth)
_THIS_DIR = pathlib.Path(__file__).resolve().parent  # scripts/data
_SCRIPTS_DIR = _THIS_DIR.parent                        # scripts/ (holds hermes_config/)
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))
from hermes_config.universe import CRYPTO_UNIVERSE  # noqa: E402

HYPERLIQUID_INFO_URL = "https://api.hyperliquid.xyz/info"

FIRST_RUN_BACKFILL_DAYS = 400                 # deep retention confirmed (~400d)
FUNDING_OVERLAP_MS = 2 * 3600 * 1000          # 2h overlap (late/finalized tail)
SLEEP_BETWEEN_COINS = 0.2                     # polite rate pacing

MAX_RETRIES = 4
RETRY_BACKOFF_BASE = 2.0                      # seconds: 2, 4, 8, 16 on 429/5xx


def _now_ms() -> int:
    return int(time.time() * 1000)


def fetch_funding_page(coin: str, start_ms: int,
                       end_ms: int | None = None) -> list[dict]:
    """POST fundingHistory; raise on HTTP!=200 (after retrying 429/5xx backoff
    like ingest_hl_bars.fetch_candles); return [] on empty. Parse to
    {time:int, funding_rate:float, premium:float} (time = 'time' ms,
    rate = float(fundingRate)). endTime is NOT used for pagination (F4)."""
    payload: dict = {"type": "fundingHistory", "coin": coin,
                     "startTime": int(start_ms)}
    if end_ms is not None:
        payload["endTime"] = int(end_ms)

    last_err: Exception | None = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            resp = requests.post(HYPERLIQUID_INFO_URL, json=payload, timeout=30)
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
        data = resp.json()
        if not isinstance(data, list) or not data:
            return []
        rows = []
        for e in data:
            rows.append({
                "time": int(e["time"]),
                "funding_rate": float(e["fundingRate"]),
                "premium": float(e["premium"]),
            })
        return rows

    if last_err is not None:
        raise last_err
    raise RuntimeError("fetch_funding_page: unreachable")


def paginate_funding(coin: str, from_ms: int, to_ms: int) -> list[dict]:
    """Walk forward: page = fetch_funding_page(coin, start); if len(page) ==
    FUNDING_PAGE, start = page[-1]['time'] (+1ms) and repeat until the page covers
    to_ms or returns short. Merge + dedup on time (ascending)."""
    merged: dict[int, dict] = {}
    start = int(from_ms)
    while True:
        page = fetch_funding_page(coin, start)
        if not page:
            break
        for r in page:
            if r["time"] < to_ms:
                merged[r["time"]] = r
        if len(page) < hl_funding_store.FUNDING_PAGE:
            break
        next_start = page[-1]["time"]
        if next_start <= start:          # safety: no forward progress
            break
        start = next_start + 1
    return [merged[t] for t in sorted(merged)]


def incremental_window(conn, coin: str) -> tuple[int, int]:
    """(start_ms, end_ms). First run (last_ts None): start = now -
    FIRST_RUN_BACKFILL_DAYS. Subsequent: start = last_ts - FUNDING_OVERLAP_MS,
    end = now."""
    now = _now_ms()
    last = hl_funding_store.last_ts(conn, coin)
    if last is None:
        return now - FIRST_RUN_BACKFILL_DAYS * 24 * 60 * 60 * 1000, now
    return last - FUNDING_OVERLAP_MS, now


def ingest_coin(conn, coin: str) -> dict:
    """paginate + append_funding + upsert_state. Returns dict with ok/new_rows/
    last_ts/window. State never mutated on a fetch failure."""
    start_ms, end_ms = incremental_window(conn, coin)
    try:
        rows = paginate_funding(coin, start_ms, end_ms)
    except Exception as e:
        return {"coin": coin, "ok": False, "error": str(e), "new_rows": 0,
                "last_ts": hl_funding_store.last_ts(conn, coin),
                "window": (start_ms, end_ms)}

    if not rows:
        return {"coin": coin, "ok": True, "error": None, "new_rows": 0,
                "last_ts": hl_funding_store.last_ts(conn, coin),
                "window": (start_ms, end_ms)}

    new_rows = hl_funding_store.append_funding(conn, coin, rows)
    max_ts = max(r["time"] for r in rows)
    existing = hl_funding_store.last_ts(conn, coin)
    final_last_ts = max(max_ts, existing) if existing is not None else max_ts
    hl_funding_store.upsert_state(
        conn, coin, final_last_ts,
        datetime.now(timezone.utc).isoformat(),
    )
    return {"coin": coin, "ok": True, "error": None, "new_rows": new_rows,
            "last_ts": final_last_ts, "window": (start_ms, end_ms)}


def ingest_all(universe: list, dry_run: bool = False) -> dict:
    """Loop ingest_coin over universe; aggregate. Polite sleep between coins."""
    results = []
    errors = []
    total_new = 0
    for i, coin in enumerate(universe):
        if dry_run:
            try:
                conn = hl_funding_store.open_store()
                start_ms, end_ms = incremental_window(conn, coin)
                conn.close()
                rows = paginate_funding(coin, start_ms, end_ms)
                results.append({"coin": coin, "ok": True,
                                "would_insert": len(rows),
                                "window": (start_ms, end_ms)})
                total_new += len(rows)
            except Exception as e:
                results.append({"coin": coin, "ok": False, "error": str(e)})
                errors.append(coin)
        else:
            conn = hl_funding_store.open_store()
            try:
                res = ingest_coin(conn, coin)
            finally:
                conn.close()
            results.append(res)
            if not res.get("ok"):
                errors.append(coin)
            else:
                total_new += res.get("new_rows", 0)
        if i < len(universe) - 1:
            time.sleep(SLEEP_BETWEEN_COINS)

    # Second-chance pass (mirrors ingest_hl_bars): re-attempt failures after a
    # quiet moment — a 35-coin seed bursts HL and often 500s the tail.
    if not dry_run and errors:
        time.sleep(RETRY_BACKOFF_BASE * 2)
        for c in list(errors):
            conn = hl_funding_store.open_store()
            try:
                res = ingest_coin(conn, c)
            finally:
                conn.close()
            if res.get("ok"):
                errors.remove(c)
                total_new += res.get("new_rows", 0)
            time.sleep(SLEEP_BETWEEN_COINS)

    return {"ok": len(errors) == 0, "errors": errors, "new_rows": total_new,
            "coins": len(universe), "results": results}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Ingest Hyperliquid funding history into the persistent store.")
    parser.add_argument("--dry-run", action="store_true",
                        help="Fetch only; do not write to the store.")
    parser.add_argument("--coins", nargs="*", default=None,
                        help="Coins to ingest (default: CRYPTO_UNIVERSE).")
    args = parser.parse_args()

    coins = args.coins if args.coins else list(CRYPTO_UNIVERSE)
    mode = "DRY-RUN" if args.dry_run else "INGEST"
    print(f"[{mode}] universe={len(coins)} coins")

    summary = ingest_all(coins, dry_run=args.dry_run)
    ok_n = len(coins) - len(summary["errors"])
    print(f"  {ok_n}/{len(coins)} ok, new_rows={summary['new_rows']}, "
          f"errors={summary['errors']}")
    return 0 if summary["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())