"""ingest_okx_liq.py — HermesForge US-186: OKX liquidation-events ingestion.

Polls OKX ``public/liquidation-orders`` (the FREE structured liquidation source —
Hyperliquid has NO public liquidation feed, flag F-A) and appends each
``details[]`` row into hl_positioning_store (the US-186 liquidation events store).

Design (per architect_us186_188_spec.md §1.3-§1.5):
  * Universe = okx_proxy.HL_TO_OKX values (32 mapped; PAXG/kBONK/kPEPE/kSHIB ->
    None -> honest gap, no liquidation feed — same policy as okx_proxy).
  * ``uly`` = instId with the '-SWAP' suffix stripped ('BTC-USDT-SWAP' ->
    'BTC-USDT'). OKX requires ``uly`` (or instFamily), NOT instId, for
    liquidation-orders.
  * ``details[]`` maps: liq_side = posSide ('long'|'short', the LIQUIDATED side),
    liq_size = sz (contracts), liq_price = bkPx, liq_ts = ts (ms).
  * sz_usd = sz * ctVal * bk_px, where ctVal is per-instrument contract
    multiplier resolved from /public/instruments and CACHED (TTL 24h) — NEVER
    hardcoded. Failure to resolve ctVal => sz_usd = NULL (do not fabricate).
  * Dedup is the heuristic composite key (flag F-C) handled by the store's
    INSERT OR IGNORE. Shallow rolling window: this feed is inherently
    "recent-window", not exhaustive — accepted (F-D = REST polling, no ws).

Usage:
    python3 ingest_okx_liq.py [--dry-run] [--inst BTC-USDT-SWAP ...]
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import pathlib
from datetime import datetime, timezone

import requests

import hl_positioning_store

# okx_proxy lives in scripts/data (same dir).
_THIS_DIR = pathlib.Path(__file__).resolve().parent
if str(_THIS_DIR) not in sys.path:
    sys.path.insert(0, str(_THIS_DIR))
from okx_proxy import HL_TO_OKX  # noqa: E402

OKX_API = "https://www.okx.com/api/v5"

CTVAL_CACHE = pathlib.Path.home() / ".hermes" / "market_data" / "okx_ctval.json"
CTVAL_TTL_S = 24 * 3600

SLEEP_BETWEEN_INST = 0.2
MAX_RETRIES = 4
RETRY_BACKOFF_BASE = 2.0


def _uly_from_inst(inst_id: str) -> str:
    """'BTC-USDT-SWAP' -> 'BTC-USDT' (strip the -SWAP suffix)."""
    return inst_id[:-len("-SWAP")] if inst_id.endswith("-SWAP") else inst_id


def load_ctvals() -> dict[str, float]:
    """instId -> ctVal (float). Cached to CTVAL_CACHE for TTL 24h; on miss/cache
    expiry, fetch /public/instruments?instType=SWAP (532 instruments, one call)
    and rebuild. Returns {} on total failure (callers then store sz_usd=NULL)."""
    now = time.time()
    if CTVAL_CACHE.exists():
        try:
            raw = json.loads(CTVAL_CACHE.read_text())
            if now - float(raw.get("fetched_at", 0.0)) < CTVAL_TTL_S:
                return {k: float(v) for k, v in raw.get("ctvals", {}).items()}
        except (ValueError, OSError, TypeError):
            pass
    ctvals: dict[str, float] = {}
    try:
        resp = requests.get(f"{OKX_API}/public/instruments",
                            params={"instType": "SWAP"}, timeout=20)
        resp.raise_for_status()
        data = resp.json().get("data") or []
        for inst in data:
            iid = inst.get("instId")
            cv = inst.get("ctVal")
            if iid and cv:
                try:
                    ctvals[iid] = float(cv)
                except (TypeError, ValueError):
                    continue
    except Exception:
        return ctvals  # partial/empty — callers store NULL, never fabricate
    try:
        CTVAL_CACHE.parent.mkdir(parents=True, exist_ok=True)
        CTVAL_CACHE.write_text(json.dumps({"fetched_at": now, "ctvals": ctvals}))
    except OSError:
        pass
    return ctvals


def fetch_liq_entries(uly: str) -> list[dict]:
    """GET public/liquidation-orders?instType=SWAP&uly=<uly>&state=filled.
    Returns the raw data[] entries (each has instId, uly, instType, totalLoss,
    details[]). Raises on HTTP != 200 after 429/5xx backoff. Returns [] on
    empty."""
    last_err: Exception | None = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            resp = requests.get(
                f"{OKX_API}/public/liquidation-orders",
                params={"instType": "SWAP", "uly": uly, "state": "filled"},
                timeout=20,
            )
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
        j = resp.json()
        if j.get("code") != "0":
            return []
        return j.get("data") or []
    if last_err is not None:
        raise last_err
    raise RuntimeError("fetch_liq_entries: unreachable")


def parse_liqs(entries: list[dict], ctvals: dict[str, float]) -> list[dict]:
    """Flatten entries[].details[] into store rows. liq_side = posSide (the
    LIQUIDATED side), side = closing-order side, sz = contracts, bk_px =
    bankruptcy price. sz_usd = sz * ctVal * bk_px (NULL if ctVal unresolved)."""
    rows = []
    for entry in entries:
        inst_id = str(entry.get("instId") or "")
        ctval = ctvals.get(inst_id)
        for d in entry.get("details") or []:
            try:
                ts = int(d.get("ts"))
                sz = float(d.get("sz"))
            except (TypeError, ValueError):
                continue
            bk_px = d.get("bkPx")
            try:
                bk_px = float(bk_px) if bk_px not in (None, "") else None
            except (TypeError, ValueError):
                bk_px = None
            sz_usd = None
            if ctval is not None and bk_px is not None:
                sz_usd = sz * ctval * bk_px
            rows.append({
                "inst_id": inst_id,
                "ts": ts,
                "pos_side": str(d.get("posSide") or ""),
                "side": str(d.get("side") or ""),
                "sz": sz,
                "sz_usd": sz_usd,
                "bk_px": bk_px,
            })
    return rows


def ingest_inst(conn, inst_id: str, ctvals: dict[str, float]) -> dict:
    """Poll one instId; append; upsert high-water mark. Never mutates state on
    a fetch failure."""
    uly = _uly_from_inst(inst_id)
    try:
        entries = fetch_liq_entries(uly)
    except Exception as e:
        return {"inst_id": inst_id, "ok": False, "error": str(e), "new_rows": 0}

    rows = parse_liqs(entries, ctvals)
    if not rows:
        return {"inst_id": inst_id, "ok": True, "error": None, "new_rows": 0,
                "events": 0}

    new_rows = hl_positioning_store.append_liqs(conn, rows)
    max_ts = max(r["ts"] for r in rows)
    existing = hl_positioning_store.last_poll_ts(conn, inst_id)
    final_ts = max(max_ts, existing) if existing is not None else max_ts
    hl_positioning_store.upsert_state(
        conn, inst_id, final_ts, datetime.now(timezone.utc).isoformat(),
    )
    return {"inst_id": inst_id, "ok": True, "error": None,
            "new_rows": new_rows, "events": len(rows)}


def ingest_all(inst_ids: list[str], dry_run: bool = False) -> dict:
    ctvals = load_ctvals()
    results = []
    errors = []
    total_new = 0
    for i, inst_id in enumerate(inst_ids):
        if dry_run:
            try:
                uly = _uly_from_inst(inst_id)
                entries = fetch_liq_entries(uly)
                n = len(parse_liqs(entries, ctvals))
                results.append({"inst_id": inst_id, "ok": True,
                                "would_insert": n})
                total_new += n
            except Exception as e:
                results.append({"inst_id": inst_id, "ok": False,
                                "error": str(e)})
                errors.append(inst_id)
        else:
            conn = hl_positioning_store.open_store()
            try:
                res = ingest_inst(conn, inst_id, ctvals)
            finally:
                conn.close()
            results.append(res)
            if not res.get("ok"):
                errors.append(inst_id)
            else:
                total_new += res.get("new_rows", 0)
        if i < len(inst_ids) - 1:
            time.sleep(SLEEP_BETWEEN_INST)
    return {"ok": len(errors) == 0, "errors": errors, "new_rows": total_new,
            "insts": len(inst_ids), "ctvals_resolved": len(ctvals),
            "results": results}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Poll OKX liquidation-orders into the positioning store.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--inst", nargs="*", default=None,
                        help="OKX instIds (default: HL_TO_OKX mapped universe)")
    args = parser.parse_args()

    if args.inst:
        inst_ids = args.inst
    else:
        inst_ids = [v for v in HL_TO_OKX.values() if v]

    mode = "DRY-RUN" if args.dry_run else "INGEST"
    summary = ingest_all(inst_ids, dry_run=args.dry_run)
    ok_n = len(inst_ids) - len(summary["errors"])
    print(f"[{mode}] {ok_n}/{len(inst_ids)} ok, new_rows={summary['new_rows']}, "
          f"ctvals_resolved={summary['ctvals_resolved']}, "
          f"errors={summary['errors']}")
    return 0 if summary["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())