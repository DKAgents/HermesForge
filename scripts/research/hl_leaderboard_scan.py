#!/usr/bin/env python3
"""
hl_leaderboard_scan.py — Hyperliquid leaderboard + top-trader fills + consistency screener

US-232. The systematic search exhausted price/positioning/flow/options classes
(one real edge: the funding carry). The untested path is COPY-trading
reverse-engineering: Hyperliquid is fully on-chain, so every trader's fills are
public + free. Pull the leaderboard, pull top traders' fills, and rank them by
genuine CONSISTENCY (NOT raw PnL) as reverse-engineering candidates.

Data sources (both free / no-auth):
  - Leaderboard:  GET  https://stats-data.hyperliquid.xyz/Mainnet/leaderboard
                  -> {"leaderboardRows": [{ethAddress, accountValue,
                       windowPerformances: [[day|week|month|allTime,
                                             {pnl, roi, vlm}], ...],
                       prize, displayName}, ...]}
                  (The plain {"type":"leaderboard",...} POST to /info fails with
                   "Failed to deserialize" — the real leaderboard is this GET.)
  - Fills:        POST https://api.hyperliquid.xyz/info
                  {"type":"userFills","user":ADDR}             -> up to 2000 recent
                  {"type":"userFillsByTime","user":ADDR,
                   "startTime":ms,"endTime":ms}               -> up to 2000 (paged)

Screener (ranks by consistency, NOT raw PnL):
  gates (hard filters):
    roi_all >= 5%            (all-time ROI bar)
    roi_30d  >  0            (still active — recent month ROI positive)
    trades   >= 50           (enough sample, not one lucky trade)
    freak_day_share <= 0.50  (no single day dominating gross PnL)
  score (0..1, higher = more consistent):
    profit factor, max drawdown (as fraction of peak equity),
    freak-day concentration, sample size (log trade count).

Storage (idempotent + resumable + rate-limit aware):
  <dir>/leaderboard_raw.json      raw leaderboard GET
  <dir>/leaderboard.json          normalized rows
  <dir>/fills/<address>.json      merged fills per trader (atomic writes)
  <dir>/screener.json             ranked screener output
  <dir>/checkpoint.json           resumable progress
  default dir = ~/.hermes/market_data/hl_copytrade/ (override with --data-dir)

Usage:
    python3 hl_leaderboard_scan.py                 # top-100, fetch + screen, print top-10
    python3 hl_leaderboard_scan.py --top 50        # top-50 traders
    python3 hl_leaderboard_scan.py --force         # re-fetch fills (ignore existing)
    python3 hl_leaderboard_scan.py --no-fetch      # screen from already-stored fills only
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

INFO_URL = "https://api.hyperliquid.xyz/info"
LEADERBOARD_URL = "https://stats-data.hyperliquid.xyz/Mainnet/leaderboard"
HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Content-Type": "application/json",
}
DEFAULT_DIR = Path.home() / ".hermes" / "market_data" / "hl_copytrade"

# ----------------------------------------------------------------------------
# Screener constants
# ----------------------------------------------------------------------------
MIN_ROI_ALL = 0.05      # all-time ROI bar (5%)
MIN_ROI_30D = 0.0       # still-active bar (recent month ROI strictly positive)
MIN_TRADES = 50         # minimum closed fills for a meaningful sample
FREAK_DAY_MAX = 0.50    # max single-day |pnl| share of gross |pnl| to pass gate
MAX_FILLS = 10000       # per-trader fill cap (empirical per-page cap is 2000)
FILL_PAGE = 2000        # observed per-request fill cap
REQUEST_DELAY_S = 0.4   # politeness delay between /info POSTs
RATE_LIMIT_BACKOFF_S = 10.0


def _log(msg: str) -> None:
    print(msg, flush=True)


def post_info(payload: dict, timeout: int = 30, retries: int = 4) -> list | None:
    """POST to the HL /info endpoint. Returns parsed JSON (list) or None on error.

    Never fabricates: returns None on any non-2xx or non-list response so the
    caller can skip that trader rather than invent data.
    """
    for attempt in range(retries):
        try:
            r = requests.post(INFO_URL, json=payload, headers=HEADERS, timeout=timeout)
        except requests.RequestException as e:
            _log(f"    post_info network error (attempt {attempt+1}): {e}")
            time.sleep(RATE_LIMIT_BACKOFF_S)
            continue
        if r.status_code == 429 or r.status_code >= 500:
            _log(f"    post_info {r.status_code} (attempt {attempt+1}), backing off")
            time.sleep(RATE_LIMIT_BACKOFF_S * (attempt + 1))
            continue
        if r.status_code != 200:
            _log(f"    post_info HTTP {r.status_code}: {r.text[:200]}")
            return None
        try:
            data = r.json()
        except ValueError:
            _log(f"    post_info non-JSON response: {r.text[:200]}")
            return None
        if isinstance(data, list):
            return data
        # error object, e.g. {"status":"err","response":"..."}
        _log(f"    post_info error response: {str(data)[:200]}")
        return None
    return None


def get_leaderboard() -> list:
    """GET the leaderboard; returns list of row dicts (already PnL-sorted)."""
    r = requests.get(LEADERBOARD_URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=60)
    r.raise_for_status()
    data = r.json()
    return data.get("leaderboardRows", [])


def _window(row: dict, name: str) -> dict:
    for key, perf in row.get("windowPerformances", []):
        if key == name:
            return perf
    return {}


def _float(v) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def normalize_leaderboard(rows: list) -> list:
    """Flatten windowPerformances into top-level numeric fields."""
    out = []
    for row in rows:
        allt = _window(row, "allTime")
        month = _window(row, "month")
        week = _window(row, "week")
        day = _window(row, "day")
        out.append({
            "ethAddress": row.get("ethAddress"),
            "accountValue": _float(row.get("accountValue")),
            "displayName": row.get("displayName"),
            "roi_all": _float(allt.get("roi")),
            "pnl_all": _float(allt.get("pnl")),
            "vlm_all": _float(allt.get("vlm")),
            "roi_30d": _float(month.get("roi")),
            "pnl_30d": _float(month.get("pnl")),
            "vlm_30d": _float(month.get("vlm")),
            "roi_7d": _float(week.get("roi")),
            "pnl_7d": _float(week.get("pnl")),
            "roi_1d": _float(day.get("roi")),
            "pnl_1d": _float(day.get("pnl")),
        })
    # leaderboard is already sorted by all-time PnL, but be explicit.
    out.sort(key=lambda r: r["pnl_all"], reverse=True)
    return out


def fetch_fills(address: str, max_fills: int = MAX_FILLS) -> list:
    """Fetch a trader's fills (fresh userFills + full userFillsByTime history).

    userFills returns the ~2000 most-recent fills (fresh). userFillsByTime
    returns fills ASCENDING (oldest first) capped per-request; page FORWARD by
    advancing startTime past the newest fill seen, so we walk the account's
    full history from genesis to now. Merge + dedup on
    (tid, hash, oid, time, coin, sz, px).
    """
    seen: set = set()
    fills: list = []

    def _add(batch: list) -> None:
        for f in batch:
            if not isinstance(f, dict):
                continue
            key = (
                f.get("tid"),
                f.get("hash"),
                f.get("oid"),
                f.get("time"),
                f.get("coin"),
                f.get("sz"),
                f.get("px"),
            )
            if key in seen:
                continue
            seen.add(key)
            fills.append(f)

    # 1) most recent (fresh)
    recent = post_info({"type": "userFills", "user": address})
    if recent:
        _add(recent)

    # 2) page FORWARD through history from genesis (startTime=0, ascending)
    end_time = int(time.time() * 1000)
    cursor = 0  # startTime
    pages = 0
    last_newest = -1
    while len(fills) < max_fills and pages < 50:
        batch = post_info({
            "type": "userFillsByTime",
            "user": address,
            "startTime": cursor,
            "endTime": end_time,
        })
        pages += 1
        if not batch:
            break
        _add(batch)
        if len(batch) < FILL_PAGE:
            break  # reached the end of available history
        # advance cursor past the NEWEST fill seen in this page (ascending order)
        newest = max((_float(f.get("time")) for f in batch if isinstance(f, dict)), default=0)
        if newest <= last_newest:
            # cursor did not advance (stale/cached response) -> stop
            break
        last_newest = newest
        cursor = int(newest) + 1
        time.sleep(REQUEST_DELAY_S)

    # sort ascending by time for stable metric computation
    fills.sort(key=lambda f: _float(f.get("time")))
    return fills


def _daily_pnl(fills: list) -> list:
    """Sum closedPnl per UTC day -> list of (day, pnl)."""
    by_day: dict = {}
    for f in fills:
        t = _float(f.get("time"))
        pnl = _float(f.get("closedPnl"))
        if t <= 0:
            continue
        day = datetime.fromtimestamp(t / 1000, timezone.utc).strftime("%Y-%m-%d")
        by_day[day] = by_day.get(day, 0.0) + pnl
    return sorted((d, p) for d, p in by_day.items())


def compute_metrics(fills: list, roi_all: float, roi_30d: float) -> dict:
    """Consistency metrics from the closedPnl series (NOT raw PnL)."""
    closed = [_float(f.get("closedPnl")) for f in fills if _float(f.get("closedPnl")) != 0.0]
    trades = len(closed)

    gross_profit = sum(p for p in closed if p > 0)
    gross_loss = -sum(p for p in closed if p < 0)
    profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else float("inf")

    # daily equity curve -> max drawdown as fraction of peak
    daily = _daily_pnl(fills)
    equity = 0.0
    peak = 0.0
    max_dd = 0.0
    for _, pnl in daily:
        equity += pnl
        peak = max(peak, equity)
        dd = peak - equity
        if peak > 0:
            max_dd = max(max_dd, dd / peak)

    # freak-day concentration: max single-day |pnl| / gross |pnl|
    daily_pnls = [p for _, p in daily]
    gross_daily = sum(abs(p) for p in daily_pnls)
    max_day = max((abs(p) for p in daily_pnls), default=0.0)
    freak_day_share = (max_day / gross_daily) if gross_daily > 0 else 1.0

    return {
        "trades": trades,
        "days_active": len(daily),
        "net_pnl": sum(closed),
        "gross_profit": gross_profit,
        "gross_loss": gross_loss,
        "profit_factor": profit_factor,
        "max_drawdown_frac": max_dd,
        "freak_day_share": freak_day_share,
        "roi_all": roi_all,
        "roi_30d": roi_30d,
    }


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def consistency_score(m: dict) -> float:
    """0..1 composite of profit factor, drawdown, freak concentration, sample.

    Raw PnL deliberately plays no part. Higher = more consistent.
    """
    import math
    pf_norm = _clamp(m["profit_factor"], 0.0, 5.0) / 5.0
    dd_norm = 1.0 - _clamp(m["max_drawdown_frac"], 0.0, 1.0)
    freak_norm = 1.0 - _clamp(m["freak_day_share"], 0.0, 1.0)
    sample_norm = _clamp(math.log10(m["trades"] + 1) / math.log10(2000 + 1), 0.0, 1.0)
    return 0.35 * pf_norm + 0.25 * dd_norm + 0.20 * freak_norm + 0.20 * sample_norm


def _atomic_write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w") as fh:
        json.dump(obj, fh)
    os.replace(tmp, path)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--top", type=int, default=100, help="top N traders by all-time PnL (default 100)")
    ap.add_argument("--data-dir", type=str, default=str(DEFAULT_DIR))
    ap.add_argument("--force", action="store_true", help="re-fetch fills even if already stored")
    ap.add_argument("--no-fetch", action="store_true", help="screen from stored fills only (no network fills)")
    ap.add_argument("--max-fills", type=int, default=MAX_FILLS)
    args = ap.parse_args()

    data_dir = Path(args.data_dir).expanduser()
    lb_raw_path = data_dir / "leaderboard_raw.json"
    lb_path = data_dir / "leaderboard.json"
    screener_path = data_dir / "screener.json"
    checkpoint_path = data_dir / "checkpoint.json"
    fills_dir = data_dir / "fills"

    # 1) leaderboard
    _log(f"[1/4] Pulling leaderboard from {LEADERBOARD_URL}")
    raw_rows = get_leaderboard()
    _atomic_write_json(lb_raw_path, {"fetchedAt": int(time.time() * 1000), "leaderboardRows": raw_rows})
    rows = normalize_leaderboard(raw_rows)
    _atomic_write_json(lb_path, {"fetchedAt": int(time.time() * 1000), "rows": rows})
    _log(f"      leaderboard rows: {len(rows)}")

    top = rows[: args.top]
    _log(f"[2/4] Fetching fills for top {len(top)} traders")

    checkpoint = {}
    if checkpoint_path.exists():
        checkpoint = json.loads(checkpoint_path.read_text())

    for i, row in enumerate(top):
        addr = row["ethAddress"]
        fpath = fills_dir / f"{addr}.json"
        if not args.force and fpath.exists():
            try:
                stored = json.loads(fpath.read_text())
                if isinstance(stored, list) and stored:
                    _log(f"      [{i+1}/{len(top)}] {addr[:10]}… cached ({len(stored)} fills)")
                    checkpoint[addr] = len(stored)
                    continue
            except (ValueError, OSError):
                pass
        if args.no_fetch:
            continue
        fills = fetch_fills(addr, max_fills=args.max_fills)
        if fills:
            _atomic_write_json(fpath, fills)
            checkpoint[addr] = len(fills)
            _log(f"      [{i+1}/{len(top)}] {addr[:10]}… {len(fills)} fills")
        else:
            _log(f"      [{i+1}/{len(top)}] {addr[:10]}… SKIPPED (no/error fills)")
        time.sleep(REQUEST_DELAY_S)

    _atomic_write_json(checkpoint_path, checkpoint)

    # 3) screen + rank
    _log("[3/4] Screening + ranking by consistency")
    screened = []
    for row in top:
        addr = row["ethAddress"]
        fpath = fills_dir / f"{addr}.json"
        if not fpath.exists():
            continue
        try:
            fills = json.loads(fpath.read_text())
        except (ValueError, OSError):
            continue
        if not isinstance(fills, list) or not fills:
            continue
        m = compute_metrics(fills, row["roi_all"], row["roi_30d"])
        m.update({
            "ethAddress": addr,
            "displayName": row["displayName"],
            "accountValue": row["accountValue"],
            "pnl_all": row["pnl_all"],
            "pnl_30d": row["pnl_30d"],
            "vlm_all": row["vlm_all"],
            "score": 0.0,
            "passed": False,
        })
        # gates
        gates = {
            "roi_all_bar": m["roi_all"] >= MIN_ROI_ALL,
            "still_active": m["roi_30d"] > MIN_ROI_30D,
            "enough_sample": m["trades"] >= MIN_TRADES,
            "no_freak_day": m["freak_day_share"] <= FREAK_DAY_MAX,
        }
        m["gates"] = gates
        m["passed"] = all(gates.values())
        if m["passed"]:
            m["score"] = consistency_score(m)
        screened.append(m)

    screened.sort(key=lambda x: (x["passed"], x["score"]), reverse=True)
    _atomic_write_json(screener_path, {
        "fetchedAt": int(time.time() * 1000),
        "constants": {
            "MIN_ROI_ALL": MIN_ROI_ALL,
            "MIN_ROI_30D": MIN_ROI_30D,
            "MIN_TRADES": MIN_TRADES,
            "FREAK_DAY_MAX": FREAK_DAY_MAX,
        },
        "ranked": screened,
    })

    # 4) emit top-10
    _log("[4/4] Ranked top-10 (consistency, NOT raw PnL)")
    top10 = [s for s in screened if s["passed"]][:10]
    _log("")
    _log(f"{'#':>2}  {'address':<44} {'roi_all':>8} {'roi_30d':>8} {'trades':>7} "
         f"{'pf':>6} {'maxDD':>6} {'score':>6}")
    for rank, s in enumerate(top10, 1):
        pf = "inf" if s["profit_factor"] == float("inf") else f"{s['profit_factor']:.2f}"
        _log(f"{rank:>2}  {s['ethAddress']:<44} {s['roi_all']*100:>7.1f}% "
             f"{s['roi_30d']*100:>7.1f}% {s['trades']:>7} {pf:>6} "
             f"{s['max_drawdown_frac']*100:>5.1f}% {s['score']:.3f}")

    if not top10:
        _log("      (no traders passed all consistency gates)")

    _log("")
    _log(f"Passed gates: {sum(1 for s in screened if s['passed'])}/{len(screened)}")
    _log(f"Stored: leaderboard -> {lb_path}")
    _log(f"        fills       -> {fills_dir}/ (n={len(checkpoint)})")
    _log(f"        screener    -> {screener_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
