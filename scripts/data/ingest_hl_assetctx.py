"""ingest_hl_assetctx.py — HermesForge US-185: Hyperliquid assetCtxs ingestion.

Snapshots ``metaAndAssetCtxs`` (all 235 non-delisted perps in ONE call) into the
persistent SQLite assetctx store (~/.hermes/market_data/hl_assetctx/), which is
the ONLY honest historical source for the real mark-vs-oracle basis — HL exposes
NO markPx/oraclePx history endpoint (F3, accepted), so the real basis can only
be accumulated going forward.

Design (per architect_us185_spec.md §2.3, mirroring ingest_hl_funding US-179):
  * ONE ``metaAndAssetCtxs`` POST returns every coin — no per-coin pagination.
  * Field names are CORRECT here: float(ctx['markPx']) / float(ctx['oraclePx'])
    (the buggy fetch_hyperliquid_metrics.py reads markPrice/oraclePrice = F1,
    out of scope, NOT copied).
  * mark_px/oracle_px are parsed with float(); missing/invalid -> None.
  * Delisted coins (meta.universe[idx]['isDelisted']) are SKIPPED.
  * Idempotent append via INSERT OR IGNORE on (coin, time); state never
    partially written (single append_snapshot commit).

Usage:
    python3 ingest_hl_assetctx.py [--dry-run]
"""

from __future__ import annotations

import argparse
import sys
import time
import pathlib

import requests

import hl_assetctx_store

HYPERLIQUID_INFO_URL = "https://api.hyperliquid.xyz/info"

# Snapshot time is bucketed to the hour so re-running the hourly cron within the
# same hour is idempotent (same (coin,time) PK -> 0 new rows), matching the
# "one snapshot per hour" cadence (US-185 §2.3 / US-186 §1.5).
SNAPSHOT_BUCKET_MS = 3600 * 1000

MAX_RETRIES = 4
RETRY_BACKOFF_BASE = 2.0        # seconds: 2, 4, 8, 16 on 429/5xx


def _now_ms() -> int:
    return int(time.time() * 1000)


def _parse_f(v) -> float | None:
    """float(), preserving None for missing/empty/non-numeric. Never raises."""
    if v is None or v == "":
        return None
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return f


def fetch_assetctxs() -> tuple[dict, list[dict]]:
    """POST metaAndAssetCtxs; return (meta, asset_ctxs) with isDelisted intact.
    meta['universe'][i] is the asset config for the i-th perp; asset_ctxs is
    INDEX-ALIGNED with meta['universe']. Raises on HTTP != 200 after 429/5xx
    backoff."""
    payload = {"type": "metaAndAssetCtxs"}
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
        if not isinstance(data, list) or len(data) < 2:
            raise RuntimeError("metaAndAssetCtxs: unexpected response shape")
        return data[0], data[1]

    if last_err is not None:
        raise last_err
    raise RuntimeError("fetch_assetctxs: unreachable")


def parse_snapshot(meta: dict, ctxs: list[dict],
                   snap_ts: int | None = None) -> list[dict]:
    """rows = [{coin, time, mark_px, oracle_px, funding, premium,
    open_interest, day_ntl_vlm, day_base_vlm, prev_day_px}] for every
    non-delisted coin. mark_px/oracle_px parsed with the CORRECT field names
    ('markPx'/'oraclePx'), not the buggy 'markPrice'/'oraclePrice' (F1). The
    day_ntl_vlm/day_base_vlm/prev_day_px fields are US-186 positioning columns
    (flag F-B: no long/short OI on HL)."""
    universe = meta.get("universe", [])
    if snap_ts is not None:
        snap_ts = int(snap_ts)
    else:
        snap_ts = (_now_ms() // SNAPSHOT_BUCKET_MS) * SNAPSHOT_BUCKET_MS
    rows = []
    for idx, ctx in enumerate(ctxs):
        cfg = universe[idx] if idx < len(universe) else {}
        if cfg.get("isDelisted"):
            continue
        coin = cfg.get("name")
        if not coin:
            continue
        rows.append({
            "coin": str(coin),
            "time": snap_ts,
            "mark_px": _parse_f(ctx.get("markPx")),
            "oracle_px": _parse_f(ctx.get("oraclePx")),
            "funding": _parse_f(ctx.get("funding")),
            "premium": _parse_f(ctx.get("premium")),
            "open_interest": _parse_f(ctx.get("openInterest")),
            "day_ntl_vlm": _parse_f(ctx.get("dayNtlVlm")),
            "day_base_vlm": _parse_f(ctx.get("dayBaseVlm")),
            "prev_day_px": _parse_f(ctx.get("prevDayPx")),
        })
    return rows


def ingest_all(dry_run: bool = False) -> dict:
    """Fetch metaAndAssetCtxs; append_snapshot (atomic). Returns
    {ok, new_rows, coins, marked_delisted, error}."""
    try:
        meta, ctxs = fetch_assetctxs()
    except Exception as e:
        return {"ok": False, "new_rows": 0, "coins": 0, "marked_delisted": 0,
                "error": str(e)}

    rows = parse_snapshot(meta, ctxs)
    if dry_run:
        return {"ok": True, "new_rows": len(rows), "coins": len(ctxs),
                "marked_delisted": len(ctxs) - len(rows), "error": None,
                "dry_run": True}

    conn = hl_assetctx_store.open_store()
    try:
        new_rows = hl_assetctx_store.append_snapshot(conn, rows)
    finally:
        conn.close()
    return {"ok": True, "new_rows": new_rows, "coins": len(ctxs),
            "marked_delisted": len(ctxs) - len(rows), "error": None}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Snapshot Hyperliquid assetCtxs into the persistent store.")
    parser.add_argument("--dry-run", action="store_true",
                        help="Fetch only; do not write to the store.")
    args = parser.parse_args()

    mode = "DRY-RUN" if args.dry_run else "INGEST"
    summary = ingest_all(dry_run=args.dry_run)
    if not summary["ok"]:
        print(f"[{mode}] FAILED: {summary['error']}")
        return 1
    print(f"[{mode}] ok, new_rows={summary['new_rows']}, "
          f"coins={summary['coins']} "
          f"(delisted={summary['marked_delisted']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())