"""ingest_crossvenue_basis.py — HermesForge US-188: HL-vs-OKX cross-venue basis.

Per mapped coin (okx_proxy.HL_TO_OKX), fetches the OKX legs and computes the
cross-venue funding-APR spread + price basis into basis_store:

  1. OKX realized 8h funding (funding-rate-history, deep ~90d backfill on first
     run, paginated backward via `before`) -> okx_funding.
  2. OKX market/ticker (last/bid/ask) -> okx_ticker.
  3. Join (per coin, hourly snapshot): HL hourly funding (hl_funding_store) vs
     OKX 8h funding (basis_store.okx_funding), and HL markPx (hl_assetctx_store)
     vs OKX last — annualized *8760 vs *1095, APR spread + price basis (bps) ->
     cross_venue_basis. This is the "real carry metric" for funding_carry.

Binance/Bybit are 403 (flag F-F) — NOT re-attempted; HL-vs-OKX only. PAXG/
kBONK/kPEPE/kSHIB (no OKX twin) -> labeled gap, skipped.

Usage:
    python3 ingest_crossvenue_basis.py [--dry-run] [--coin BTC ETH ...]
"""

from __future__ import annotations

import argparse
import sys
import time
import pathlib
from datetime import datetime, timezone

import requests

import basis_store
import hl_funding_store
import hl_assetctx_store
import spot_basis_store

_THIS_DIR = pathlib.Path(__file__).resolve().parent
if str(_THIS_DIR) not in sys.path:
    sys.path.insert(0, str(_THIS_DIR))
from okx_proxy import HL_TO_OKX  # noqa: E402

OKX_API = "https://www.okx.com/api/v5"

BACKFILL_DAYS = 90
SNAPSHOT_BUCKET_MS = 3600 * 1000
MAX_PAGES = 12
SLEEP_BETWEEN_COINS = 0.2
MAX_RETRIES = 4
RETRY_BACKOFF_BASE = 2.0

HOURS_PER_YEAR = 8760
OKX_8H_PER_YEAR = 365 * 3   # 1095


def _now_ms() -> int:
    return int(time.time() * 1000)


def _get(path: str, params: dict) -> dict:
    last_err: Exception | None = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            resp = requests.get(f"{OKX_API}{path}", params=params, timeout=20)
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


def fetch_funding_history(inst_id: str, after: int | None = None) -> list[dict]:
    """Realized 8h funding (newest-first). Returns [{fundingTime, realizedRate}].
    ``after`` pages BACKWARD to older settlements (OKX convention: ``after`` =
    records earlier than ts, verified live — the spec's "before" is inverted)."""
    params: dict = {"instId": inst_id, "limit": "100"}
    if after is not None:
        params["after"] = str(after)
    j = _get("/public/funding-rate-history", params)
    if j.get("code") != "0":
        return []
    out = []
    for e in j.get("data") or []:
        try:
            ts = int(e["fundingTime"])
            rate = float(e["realizedRate"])
        except (TypeError, ValueError, KeyError):
            continue
        out.append({"fundingTime": ts, "realizedRate": rate})
    return out


def backfill_okx_funding(inst_id: str, cutoff_ms: int) -> list[dict]:
    """Paginate funding-rate-history BACKWARD (via ``after``) to cutoff_ms
    (~90d). Dedup on ts. Returns [{inst_id, ts, funding_rate, premium:None}]
    ascending."""
    merged: dict[int, float] = {}
    after: int | None = None
    for _ in range(MAX_PAGES):
        page = fetch_funding_history(inst_id, after)
        if not page:
            break
        oldest = page[-1]["fundingTime"]
        for e in page:
            merged[e["fundingTime"]] = e["realizedRate"]
        if oldest <= cutoff_ms:
            break
        if after is not None and oldest >= after:
            break  # no backward progress
        after = oldest
    return [{"inst_id": inst_id, "ts": ts, "funding_rate": rate,
             "premium": None} for ts, rate in sorted(merged.items())]


def fetch_okx_ticker(inst_id: str) -> dict | None:
    j = _get("/market/ticker", {"instId": inst_id})
    if j.get("code") != "0" or not j.get("data"):
        return None
    d = j["data"][0]
    try:
        last = float(d["last"])
        bid = float(d["bidPx"]) if d.get("bidPx") not in (None, "") else None
        ask = float(d["askPx"]) if d.get("askPx") not in (None, "") else None
    except (TypeError, ValueError, KeyError):
        return None
    return {"inst_id": inst_id, "ts": ((_now_ms() // SNAPSHOT_BUCKET_MS)
                                       * SNAPSHOT_BUCKET_MS),
            "last": last, "bid": bid, "ask": ask}


def _latest_hl_funding(coin: str) -> float | None:
    df = hl_funding_store.read_funding(coin)
    if df.empty:
        return None
    try:
        return float(df["funding_rate"].iloc[-1])
    except (IndexError, ValueError):
        return None


def _latest_hl_mark(coin: str) -> float | None:
    df = hl_assetctx_store.read_basis(coin)
    if df.empty or df["mark_px"].iloc[-1] is None:
        return None
    try:
        return float(df["mark_px"].iloc[-1])
    except (IndexError, ValueError):
        return None


def _latest_hl_oracle(coin: str) -> float | None:
    """Latest HL perp oracle price (assetCtxs oraclePx) — the spot-basis oracle."""
    df = hl_assetctx_store.read_basis(coin)
    if df.empty or df["oracle_px"].iloc[-1] is None:
        return None
    try:
        return float(df["oracle_px"].iloc[-1])
    except (IndexError, ValueError):
        return None


def ingest_coin(conn, coin: str, inst_id: str, dry_run: bool) -> dict:
    # 1. OKX funding backfill / incremental
    okf_last = basis_store.last_ts(conn, "okx_funding", inst_id)
    if okf_last is None:
        funding_rows = backfill_okx_funding(
            inst_id, _now_ms() - BACKFILL_DAYS * 24 * 3600 * 1000)
    else:
        page = fetch_funding_history(inst_id)
        funding_rows = [{"inst_id": inst_id, "ts": e["fundingTime"],
                         "funding_rate": e["realizedRate"], "premium": None}
                        for e in page]

    # 2. OKX ticker
    ticker = fetch_okx_ticker(inst_id)

    # 3. join (HL leg vs OKX leg)
    snap_ts = (_now_ms() // SNAPSHOT_BUCKET_MS) * SNAPSHOT_BUCKET_MS
    hl_rate = _latest_hl_funding(coin)
    hl_mark = _latest_hl_mark(coin)
    # Latest OKX 8h rate = the newest settlement just fetched (NOT read from the
    # store, which is still empty on the first run).
    okx_rate = None
    if funding_rows:
        okx_rate = max(funding_rows, key=lambda r: r["ts"])["funding_rate"]
    basis_row = None
    if hl_rate is not None and okx_rate is not None and okx_rate != 0.0 \
            and hl_mark is not None and ticker is not None:
        hl_apr = hl_rate * HOURS_PER_YEAR * 100.0
        okx_apr = okx_rate * OKX_8H_PER_YEAR * 100.0
        spread = hl_apr - okx_apr
        px_basis = (hl_mark - ticker["last"]) / ticker["last"] * 1e4
        basis_row = {"coin": coin, "ts": snap_ts, "hl_funding_apr": hl_apr,
                     "okx_funding_apr": okx_apr, "funding_spread_apr": spread,
                     "hl_mark": hl_mark, "okx_last": ticker["last"],
                     "price_basis_bps": px_basis}

    if dry_run:
        return {"coin": coin, "ok": True, "funding_rows": len(funding_rows),
                "ticker": ticker is not None,
                "basis": basis_row is not None}

    new_funding = basis_store.append_okx_funding(conn, funding_rows)
    new_ticker = basis_store.append_okx_ticker(
        conn, [ticker]) if ticker else 0
    new_basis = basis_store.append_basis(
        conn, [basis_row]) if basis_row else 0

    # US-229 spot-basis accumulation: real OKX last vs HL oracle (the UNMEASURED
    # hedge input). Accumulate going forward so the delta-neutral hedge stops
    # being proxied by the oracle over the paper-forward window. spot_basis_bps
    # is COMPUTED inside the store (never caller-supplied, never silently
    # credited as a fill).
    spot_row = None
    if ticker is not None and ticker.get("last") is not None:
        oracle = _latest_hl_oracle(coin)
        if oracle is not None:
            spot_row = {"coin": coin, "time": ticker["ts"],
                        "spot_px": ticker["last"], "oracle_px": oracle}
    new_spot = spot_basis_store.append_spot_basis(conn, [spot_row]) if spot_row else 0

    iso = datetime.now(timezone.utc).isoformat()
    if funding_rows:
        basis_store.upsert_state(conn, "okx_funding", inst_id,
                                 max(r["ts"] for r in funding_rows), iso)
    if ticker:
        basis_store.upsert_state(conn, "okx_ticker", inst_id, ticker["ts"], iso)
    if basis_row:
        basis_store.upsert_state(conn, "basis", coin, snap_ts, iso)

    return {"coin": coin, "ok": True, "new_funding": new_funding,
            "new_ticker": new_ticker, "new_basis": new_basis,
            "new_spot": new_spot, "basis_computed": basis_row is not None,
            "spot_computed": spot_row is not None}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Ingest HL-vs-OKX cross-venue basis into basis_store.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--coin", nargs="*", default=None)
    args = parser.parse_args()

    if args.coin:
        pairs = [(c, HL_TO_OKX[c]) for c in args.coin if HL_TO_OKX.get(c)]
    else:
        pairs = [(c, i) for c, i in HL_TO_OKX.items() if i]

    mode = "DRY-RUN" if args.dry_run else "INGEST"
    conn = basis_store.open_store()
    try:
        ok = 0
        computed = 0
        for i, (coin, inst_id) in enumerate(pairs):
            try:
                res = ingest_coin(conn, coin, inst_id, args.dry_run)
            except Exception as e:
                print(f"  {coin} FAILED: {e}")
                continue
            ok += 1
            if res.get("basis_computed") or res.get("basis"):
                computed += 1
            if args.dry_run:
                print(f"  {coin}: funding_rows={res['funding_rows']}, "
                      f"ticker={res['ticker']}, basis={res['basis']}")
            else:
                print(f"  {coin}: new_funding={res['new_funding']}, "
                      f"new_ticker={res['new_ticker']}, "
                      f"new_basis={res['new_basis']}, "
                      f"new_spot={res['new_spot']}")
            if i < len(pairs) - 1:
                time.sleep(SLEEP_BETWEEN_COINS)
    finally:
        conn.close()
    print(f"[{mode}] {ok}/{len(pairs)} ok, basis_computed={computed}")
    return 0


if __name__ == "__main__":
    sys.exit(main())