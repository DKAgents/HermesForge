"""backfill_okx_proxy.py — HermesForge US-198: labeled OKX-proxy 5m backfill.

Hyperliquid's public S3 archive of deep 5m history is REQUESTER-PAYS. The
estimator (see reports/data-depth-backfill-US-198.md) prices the full-universe
depth in the single-digit cents range, but access requires a billable AWS
account; this deployment has only Cloudflare R2 credentials, and the bucket
rejects anonymous requester-pays requests (HTTP 403 — treated as permanent, no
geo/VPN circumvention). Therefore the S3 path is STOPPED and this module is the
documented fallback: it persists DEEP 5m bars from OKX's public
`history-candles` endpoint into the bar store, every row labeled
source='okx_proxy'.

Design (mirrors ingest_hl_bars / ingest_hl_funding):
  * Universe from hermes_config.universe CRYPTO_UNIVERSE (single source of truth).
  * Only fills the PRE-STORE gap: bars strictly OLDER than the store's existing
    floor (min_ts) — never overlaps or rewrites same-venue bars. Since the PK
    is (ticker, timeframe, ts), INSERT OR IGNORE keeps the whole operation
    idempotent and atomic (never partial).
  * Unmapped tickers (kBONK/kPEPE/kSHIB/PAXG — no OKX perp twin) are skipped and
    reported as proxy gaps; NO bars are fabricated.
  * OKX `history-candles` 5m reaches back ~139 days (verified live, 2026-11-02).

Usage:
    python3 backfill_okx_proxy.py [--dry-run] [--coins BTC ETH ...] [--days 140]
"""

from __future__ import annotations

import argparse
import sys
import time
import pathlib
from datetime import datetime, timezone

_THIS_DIR = pathlib.Path(__file__).resolve().parent  # scripts/data
_SCRIPTS_DIR = _THIS_DIR.parent                        # scripts/ (hermes_config/)
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))
if str(_THIS_DIR) not in sys.path:
    sys.path.insert(0, str(_THIS_DIR))

import hl_bar_store                     # noqa: E402
import okx_proxy                        # noqa: E402
from hermes_config.universe import CRYPTO_UNIVERSE  # noqa: E402

DEFAULT_LOOKBACK_DAYS = 140             # OKX 5m history-candles depth (~139d)
SLEEP_BETWEEN_TICKERS = 0.4             # be gentle on OKX rate limits


def _now_ms() -> int:
    return int(time.time() * 1000)


def backfill_ticker(conn, ticker: str, timeframe: str,
                    lookback_days: int) -> dict:
    """Fetch OKX bars for [now - lookback_days, store_floor) and append them
    labeled source='okx_proxy'. Returns a status dict. Never mutates state on a
    fetch failure; INSERT OR IGNORE means re-runs insert 0 for existing keys."""
    floor = hl_bar_store.coverage(conn, ticker, timeframe)["min_ts"]
    end_ms = floor if floor is not None else _now_ms()
    start_ms = _now_ms() - lookback_days * 86400_000

    if okx_proxy.HL_TO_OKX.get(ticker) is None:
        return {"ticker": ticker, "ok": False, "gap": True, "new_bars": 0,
                "reason": "unmapped (no OKX perp twin)"}

    if end_ms <= start_ms:
        return {"ticker": ticker, "ok": True, "gap": False, "new_bars": 0,
                "reason": "no pre-store window to fill"}

    try:
        df = okx_proxy.fetch_okx_bars(ticker, timeframe, start_ms, end_ms)
    except Exception as e:
        return {"ticker": ticker, "ok": False, "gap": False, "new_bars": 0,
                "reason": f"fetch error: {e}"}

    if df is None or df.empty:
        return {"ticker": ticker, "ok": True, "gap": False, "new_bars": 0,
                "reason": "no OKX data in window"}

    bars = df.to_dict("records")
    new_bars = hl_bar_store.append_bars(
        conn, ticker, timeframe, bars, source=hl_bar_store.BarSource.OKX_PROXY)
    return {"ticker": ticker, "ok": True, "gap": False, "new_bars": new_bars,
            "reason": "ok"}


def backfill_all(coins: list, timeframe: str, lookback_days: int,
                 dry_run: bool) -> dict:
    results, errors, gaps, total_new = [], [], [], 0
    for i, t in enumerate(coins):
        if dry_run:
            inst = okx_proxy.HL_TO_OKX.get(t)
            results.append({"ticker": t, "ok": inst is not None,
                            "gap": inst is None, "new_bars": 0,
                            "reason": "unmapped" if inst is None else "would fetch"})
            if inst is None:
                gaps.append(t)
        else:
            conn = hl_bar_store.open_store(timeframe)
            try:
                res = backfill_ticker(conn, t, timeframe, lookback_days)
            finally:
                conn.close()
            results.append(res)
            if not res["ok"]:
                errors.append(t)
            if res.get("gap"):
                gaps.append(t)
            total_new += res.get("new_bars", 0)
        if i < len(coins) - 1:
            time.sleep(SLEEP_BETWEEN_TICKERS)
    return {"ok": len(errors) == 0, "errors": errors, "gaps": gaps,
            "new_bars": total_new, "coins": len(coins), "results": results}


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Backfill deep 5m bars from the OKX proxy (labeled okx_proxy).")
    ap.add_argument("--dry-run", action="store_true", help="Report only; no write.")
    ap.add_argument("--coins", nargs="*", default=None,
                    help="Coins to backfill (default: CRYPTO_UNIVERSE).")
    ap.add_argument("--days", type=int, default=DEFAULT_LOOKBACK_DAYS,
                    help="Lookback depth in days (default 140).")
    ap.add_argument("--timeframe", default="5m", help="Bar timeframe.")
    args = ap.parse_args()

    coins = args.coins if args.coins else list(CRYPTO_UNIVERSE)
    mode = "DRY-RUN" if args.dry_run else "BACKFILL"
    print(f"[{mode}] coins={len(coins)} lookback={args.days}d tf={args.timeframe}")

    summary = backfill_all(coins, args.timeframe, args.days, dry_run=args.dry_run)
    ok_n = summary["coins"] - len(summary["errors"])
    print(f"  {ok_n}/{summary['coins']} ok, new_bars={summary['new_bars']}, "
          f"proxy_gaps={summary['gaps']}, errors={summary['errors']}")
    return 0 if summary["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())