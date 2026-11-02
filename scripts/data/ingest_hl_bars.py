"""
ingest_hl_bars.py — HermesForge US-177: daily Hyperliquid 5m bar ingestion.

Incrementally ingests Hyperliquid candle OHLCV into the persistent SQLite bar
store (~/.hermes/market_data/hl_bars/), closing the exact gap where existing
intraday caches are TTL-OVERWRITTEN (never accumulate) and therefore cannot
serve a rolling same-venue backtest window.

Design (per architect_us177_spec.md):
  * Universe is imported from hermes_config.universe CRYPTO_UNIVERSE — the
    single source of truth (never re-listed).
  * 5m is the mandatory trading resolution (STR-Q intraday; the 17-day
    retention-cliff interval). 1d is the daily resolution (lower-frequency
    backtests, e.g. cross-sectional momentum).
  * Incremental + idempotent: high-water-mark window with a 2-bar overlap to
    catch late/finalized tails; append via INSERT OR IGNORE dedups re-fetched
    overlaps to zero new rows.
  * First run seeds ~18 days (bounded by Hyperliquid's ~17-day 5m retention).
  * State is only mutated AFTER a fully-successful page (never partial).

Usage:
    python3 ingest_hl_bars.py [--dry-run] [--timeframes 5m 15m ...]
"""

from __future__ import annotations

import argparse
import sys
import time
import pathlib
from datetime import datetime, timezone

import requests

import hl_bar_store

# Universe (single source of truth) ---------------------------------------------------  # noqa: E501
_THIS_DIR = pathlib.Path(__file__).resolve().parent  # scripts/data
_SCRIPTS_DIR = _THIS_DIR.parent                        # scripts/  (holds hermes_config/)
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))
from hermes_config.universe import CRYPTO_UNIVERSE  # noqa: E402

HYPERLIQUID_INFO_URL = "https://api.hyperliquid.xyz/info"

INGEST_TIMEFRAMES = ["5m", "1d"]            # 5m trading + 1d daily resolution
FIRST_RUN_LOOKBACK_DAYS = 18                # seed slightly beyond ~17d retention
INCREMENTAL_OVERLAP_MS = 2 * 5 * 60 * 1000  # 2 bars overlap (late/finalized tail)
SLEEP_BETWEEN_TICKERS = 0.2                 # polite rate pacing (existing convention)


def _now_ms() -> int:
    return int(time.time() * 1000)


MAX_RETRIES = 4
RETRY_BACKOFF_BASE = 2.0  # seconds; exponential: 2, 4, 8, 16 on 429/5xx


def fetch_candles(ticker: str, interval: str, start_ms: int,
                  end_ms: int) -> list[dict]:
    """POST candleSnapshot; raise on HTTP!=200 (after retrying rate-limit/5xx);
    return [] on empty. Parse to {ts, open, high, low, close, volume, trades}
    (ts = bar open ms epoch). Hyperliquid rate-limits bursts of heavy window
    fetches with HTTP 429 — retry with exponential backoff."""
    payload = {
        "type": "candleSnapshot",
        "req": {
            "coin": ticker,  # exact canonical case (HL coin names case-sensitive)
            "interval": interval,
            "startTime": int(start_ms),
            "endTime": int(end_ms),
        },
    }
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
        bars = []
        for c in data:
            bars.append({
                "ts": int(c["t"]),
                "open": float(c["o"]),
                "high": float(c["h"]),
                "low": float(c["l"]),
                "close": float(c["c"]),
                "volume": float(c["v"]),
                "trades": int(c["n"]) if c.get("n") is not None else None,
            })
        return bars
    if last_err is not None:
        raise last_err
    raise RuntimeError("fetch_candles: unreachable")


def _fetch_window(ticker: str, interval: str, start_ms: int,
                  end_ms: int) -> list[dict]:
    """Return bars in [start_ms, end_ms) ascending. A single candleSnapshot
    call returns Hyperliquid's ENTIRE retained floor (~17.5 days for 5m) in one
    response regardless of startTime, so no pagination is needed for the
    18-day first-run seed — and for incremental (subsequent) runs the window is
    only ~1 day. A walk-back would issue a redundant second request that
    doubles burst load and trips Hyperliquid's rate limiter (observed 500s).

    The window filter is still applied here so the store never records bars
    outside the incremental window."""
    page = fetch_candles(ticker, interval, start_ms, end_ms)
    merged: dict[int, dict] = {
        b["ts"]: b for b in page if start_ms <= b["ts"] < end_ms
    }
    return [merged[ts] for ts in sorted(merged)]


def incremental_window(conn, ticker: str, timeframe: str) -> tuple[int, int]:
    """(start_ms, end_ms) for this run.
    - first run (last_ts() is None): start = now - FIRST_RUN_LOOKBACK_DAYS
      (seed the full retained window; HL bounds the actual reach).
    - subsequent: start = last_ts - INCREMENTAL_OVERLAP_MS (catch tail)."""
    now = _now_ms()
    last = hl_bar_store.last_ts(conn, ticker, timeframe)
    if last is None:
        return now - FIRST_RUN_LOOKBACK_DAYS * 24 * 60 * 60 * 1000, now
    return last - INCREMENTAL_OVERLAP_MS, now


def ingest_ticker(conn, ticker: str, timeframe: str) -> dict:
    """Paginate fetch from incremental_window()->start to now, append_bars(),
    upsert_state(). Returns {'ticker','timeframe','new_bars','last_ts','window'}.
    Never mutates state on a fetch failure (append only after a full successful
    page)."""
    start_ms, end_ms = incremental_window(conn, ticker, timeframe)
    # ticker kept as exact canonical case (HL coin names are case-sensitive).
    try:
        bars = _fetch_window(ticker, timeframe, start_ms, end_ms)
    except Exception as e:
        return {"ticker": ticker, "timeframe": timeframe, "ok": False,
                "error": str(e), "new_bars": 0, "last_ts": None,
                "window": (start_ms, end_ms)}

    if not bars:
        # Nothing new returned (never ingested or no data in window) — do not
        # mutate state; a later run will re-seed from the back-off window.
        return {"ticker": ticker, "timeframe": timeframe, "ok": True,
                "error": None, "new_bars": 0,
                "last_ts": hl_bar_store.last_ts(conn, ticker, timeframe),
                "window": (start_ms, end_ms)}

    new_bars = hl_bar_store.append_bars(conn, ticker, timeframe, bars)
    max_ts = max(b["ts"] for b in bars)
    existing = hl_bar_store.last_ts(conn, ticker, timeframe)
    final_last_ts = max(max_ts, existing) if existing is not None else max_ts
    hl_bar_store.upsert_state(
        conn, ticker, timeframe, final_last_ts,
        datetime.now(timezone.utc).isoformat(),
    )
    return {"ticker": ticker, "timeframe": timeframe, "ok": True,
            "error": None, "new_bars": new_bars, "last_ts": final_last_ts,
            "window": (start_ms, end_ms)}


def ingest_timeframe(timeframe: str, universe: list, dry_run: bool = False) -> dict:
    """Loop ingest_ticker over universe; aggregate {'ok','errors','new_bars',
    'tickers', 'results'}. Polite sleep between tickers."""
    results = []
    errors = []
    total_new = 0
    for i, ticker in enumerate(universe):
        if dry_run:
            # Fetch only (no DB write). Report the window we WOULD ingest.
            try:
                conn = hl_bar_store.open_store(timeframe)
                start_ms, end_ms = incremental_window(conn, ticker, timeframe)
                conn.close()
                bars = _fetch_window(ticker, timeframe, start_ms, end_ms)
                results.append({"ticker": ticker, "ok": True,
                                "would_insert": len(bars),
                                "window": (start_ms, end_ms)})
                total_new += len(bars)
            except Exception as e:
                results.append({"ticker": ticker, "ok": False, "error": str(e)})
                errors.append(ticker)
        else:
            conn = hl_bar_store.open_store(timeframe)
            try:
                res = ingest_ticker(conn, ticker, timeframe)
            finally:
                conn.close()
            results.append(res)
            if not res.get("ok"):
                errors.append(ticker)
            else:
                total_new += res.get("new_bars", 0)
        if i < len(universe) - 1:
            time.sleep(SLEEP_BETWEEN_TICKERS)

    # Second-chance pass: re-attempt any failed ticker after a cooldown (a
    # 35-ticker seed bursts Hyperliquid and its rate limiter most often 500s
    # the last few alphabetically-odd tickers; they self-heal on a quiet retry).
    if not dry_run and errors:
        time.sleep(RETRY_BACKOFF_BASE * 2)  # moment of quiet before retry
        for t in list(errors):
            conn = hl_bar_store.open_store(timeframe)
            try:
                res = ingest_ticker(conn, t, timeframe)
            finally:
                conn.close()
            if res.get("ok"):
                errors.remove(t)
                total_new += res.get("new_bars", 0)
            time.sleep(SLEEP_BETWEEN_TICKERS)

    return {"timeframe": timeframe, "ok": len(errors) == 0,
            "errors": errors, "new_bars": total_new, "tickers": len(universe),
            "results": results}


def main() -> int:
    parser = argparse.ArgumentParser(description="Ingest Hyperliquid bars into the persistent store.")
    parser.add_argument("--dry-run", action="store_true",
                        help="Fetch only; do not write to the store.")
    parser.add_argument("--timeframes", nargs="*", default=None,
                        help="Timeframes to ingest (default: 5m).")
    args = parser.parse_args()

    timeframes = args.timeframes if args.timeframes else INGEST_TIMEFRAMES
    mode = "DRY-RUN" if args.dry_run else "INGEST"
    print(f"[{mode}] universe={len(CRYPTO_UNIVERSE)} tickers, "
          f"timeframes={timeframes}")

    all_failed = True
    for tf in timeframes:
        summary = ingest_timeframe(tf, list(CRYPTO_UNIVERSE), dry_run=args.dry_run)
        total = summary["tickers"]
        ok_n = total - len(summary["errors"])
        print(f"  {tf}: {ok_n}/{total} ok, new_bars={summary['new_bars']}, "
              f"errors={summary['errors']}")
        if summary["ok"]:
            all_failed = False

    return 0 if not all_failed else 1


if __name__ == "__main__":
    sys.exit(main())