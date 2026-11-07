"""ingest_deribit_options_history.py — HermesForge US-231 backfill driver.

Backfills the VRP (HYP-30) dataset from the FREE, no-auth Deribit public REST
surface. Enumerates expired BTC/ETH option instruments, pulls their trade
history (via ``get_last_trades_by_currency_and_time`` — all options of a
currency in one call), and reconstructs a DAILY ATM-straddle PREMIUM series from
Deribit's own quoted ``mark_price`` / ``mark_iv`` / ``index_price`` tags (no
Black-Scholes inversion, nothing fabricated). Also backfills DVOL (vol-index)
into ``iv_store.dvol_index`` and computes a realized-vol series from the
reconstructed underlying index closes.

PROVENANCE (the load-bearing guarantee):
  * premium  = Deribit ``mark_price`` (fair option premium), NOT a BS solve
  * atm_iv   = Deribit ``mark_iv`` (%), averaged call+put; NULL when iv is 0/missing
  * spot     = Deribit ``index_price``
  * realized = our std-of-log-returns over the reconstructed index series (30d)
  * dvol     = Deribit DVOL close

Idempotent (PK dedup) + resumable (per-day checkpoint in day_state).

Usage:
    python3 ingest_deribit_options_history.py [--currency BTC ETH]
        [--years 2.0] [--periods week month] [--dry-run]
        [--skip-dvol] [--limit-days N]
"""

from __future__ import annotations

import argparse
import collections
import math
import pathlib
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

import requests

_THIS_DIR = pathlib.Path(__file__).resolve().parent          # scripts/data
if str(_THIS_DIR) not in sys.path:
    sys.path.insert(0, str(_THIS_DIR))

import options_history as oh   # noqa: E402
import iv_store                # noqa: E402

HISTORY = "https://history.deribit.com/api/v2/public"
DERIBIT = "https://www.deribit.com/api/v2/public"

MS_PER_DAY = 86_400_000
MAX_RETRIES = 6
RETRY_BACKOFF_BASE = 2.0
RATE_LIMIT_PAUSE = 0.05        # ~20 rps ceiling (history API ~20 rps)
WORKERS = 8
TRADE_PAGE = 10_000            # max count for get_last_trades_by_currency_and_time

DVOL_START_MS = 1614556800000   # 2021-03-01 (DVOL data begins ~2021-05; earlier is empty)
DVOL_CHUNK_MS = 30 * MS_PER_DAY
CURRENCIES = ("BTC", "ETH")
DEFAULT_PERIODS = ("week", "month")
REALIZED_WINDOW_DAYS = 30       # matches vol_vrp.REALIZED_VOL_LOOKBACK_DAYS
DAYS_PER_YEAR = 365.0

# global request throttle (thread-safe) — keeps aggregate rate ~<= 20 rps
_throttle_lock = threading.Lock()
_last_req = 0.0


def _throttle() -> None:
    global _last_req
    with _throttle_lock:
        now = time.monotonic()
        wait = RATE_LIMIT_PAUSE - (now - _last_req)
        if wait > 0:
            time.sleep(wait)
        _last_req = time.monotonic()


def _now_ms() -> int:
    return int(time.time() * 1000)


def _day_of(ms: int) -> int:
    return int(ms) // MS_PER_DAY * MS_PER_DAY


def _get(base: str, path: str, params: dict, session: requests.Session) -> dict:
    last_err: Exception | None = None
    for attempt in range(MAX_RETRIES + 1):
        _throttle()
        try:
            resp = session.get(f"{base}{path}", params=params, timeout=120)
        except requests.RequestException as e:
            last_err = e
            time.sleep(RETRY_BACKOFF_BASE * (2 ** attempt))
            continue
        if resp.status_code == 429 or resp.status_code >= 500:
            last_err = RuntimeError(f"HTTP {resp.status_code}")
            time.sleep(RETRY_BACKOFF_BASE * (2 ** attempt))
            continue
        resp.raise_for_status()
        return resp.json()
    raise last_err if last_err else RuntimeError("_get: unreachable")


def fetch_instruments(currency: str, expired: str,
                      session: requests.Session) -> list[dict]:
    j = _get(HISTORY, "/get_instruments",
             {"currency": currency, "kind": "option", "expired": expired}, session)
    return j.get("result") or []


def build_inst_map(currency: str, periods: tuple[str, ...], start_cut: int,
                   session: requests.Session) -> dict[str, tuple[int, float, str]]:
    """instrument_name -> (expiry, strike, option_type) for week/month options
    whose expiry is within [start_cut, now]. Expired + currently-live catalogues
    are BOTH consulted so near-dated (but not yet expired) maturities are usable
    at the tail of the window; the reconstruction itself only uses SETTLED days
    via dte survival."""
    inst_map: dict[str, tuple[int, float, str]] = {}
    seen: set[str] = set()
    for expired in ("true", "false"):
        for i in fetch_instruments(currency, expired, session):
            name = i.get("instrument_name")
            otype = i.get("option_type")
            strike = i.get("strike")
            expiry = i.get("expiration_timestamp")
            if (not name or name in seen or otype not in ("call", "put")
                    or strike is None or expiry is None
                    or i.get("settlement_period") not in periods):
                continue
            if int(expiry) < start_cut:
                continue
            seen.add(name)
            inst_map[name] = (int(expiry), float(strike), otype)
    return inst_map


def fetch_day_trades(currency: str, day_start: int,
                     session: requests.Session) -> list[dict]:
    """All option trades for a currency over [day_start, day_start+1d), paging
    backwards in time until has_more stops."""
    out: list[dict] = []
    end = day_start + MS_PER_DAY - 1
    while True:
        j = _get(HISTORY, "/get_last_trades_by_currency_and_time",
                 {"currency": currency, "kind": "option",
                  "start_timestamp": day_start, "end_timestamp": end,
                  "count": TRADE_PAGE}, session)
        res = j.get("result") or {}
        trades = res.get("trades") or []
        if not trades:
            break
        out.extend(trades)
        if not res.get("has_more"):
            break
        end = min(int(t["timestamp"]) for t in trades) - 1
        if end <= day_start:
            break
    return out


def process_day(currency: str, day: int, trades: list[dict],
                inst_map: dict[str, tuple[int, float, str]]) -> tuple[list[dict], list[dict]]:
    """Reconstruct the day's ATM straddle rows + the underlying close from a
    day's worth of currency-wide trades.

    For each (expiry, strike) we keep the LATEST trade's mark_price/mark_iv; the
    ATM strike is the one nearest that day's underlying `index_price`. Only days
    where BOTH the ATM call and put traded (hence carry a Deribit mark) produce a
    straddle row — a day with no observable premium is SKIPPED, never fabricated.
    """
    # (expiry, strike) -> { 'call': (mark, iv, ts), 'put': (...) }
    marks: dict[tuple[int, float], dict] = {}
    # latest underlying index observation of the day
    latest_index: tuple[int, float] | None = None

    for t in trades:
        name = t.get("instrument_name")
        meta = inst_map.get(name)
        if meta is None:
            continue  # not a week/month instrument in our window
        expiry, strike, otype = meta
        try:
            ts = int(t["timestamp"])
            mp = float(t["mark_price"])
            iv = float(t["iv"])
            ip = float(t["index_price"])
        except (TypeError, ValueError, KeyError):
            continue
        if mp is None or ip is None or ip <= 0:
            continue
        key = (expiry, strike)
        slot = marks.setdefault(key, {})
        if otype not in slot or ts >= slot[otype][2]:
            slot[otype] = (mp, iv if iv > 0 else None, ts)
        if latest_index is None or ts >= latest_index[0]:
            latest_index = (ts, ip)

    if latest_index is None:
        return [], []
    snap_ts, underlying = latest_index

    by_expiry: dict[int, dict] = collections.defaultdict(dict)
    for (expiry, strike), slot in marks.items():
        by_expiry[expiry][strike] = slot

    under_rows: list[dict] = [{"currency": currency, "day": day, "close": underlying}]
    strad_rows: list[dict] = []
    for expiry, strikes in by_expiry.items():
        candidates = [k for k, slot in strikes.items()
                      if slot.get("call") is not None and slot.get("put") is not None]
        if not candidates:
            continue
        atm_strike = min(candidates, key=lambda k: abs(k - underlying))
        a_call = strikes[atm_strike]["call"]
        a_put = strikes[atm_strike]["put"]
        cm, civ, _ = a_call
        pm, piv, _ = a_put
        if cm is None or pm is None:
            continue
        atm_iv = None
        iv_source = None
        if civ is not None and piv is not None:
            atm_iv = 0.5 * (civ + piv)
            iv_source = oh.MARK_SOURCE
        dte = (expiry - snap_ts) / MS_PER_DAY
        if dte <= 0:
            continue  # post-expiry snapshot — not a tradeable straddle
        strad_rows.append({
            "currency": currency, "expiry": expiry, "day": day, "snap_ts": snap_ts,
            "dte": round(dte, 6), "underlying": underlying, "strike": atm_strike,
            "call_premium": cm, "put_premium": pm,
            "atm_straddle_premium": cm + pm, "atm_iv": atm_iv, "iv_source": iv_source,
        })
    return under_rows, strad_rows


def fetch_dvol_all(currency: str, session: requests.Session) -> list[dict]:
    """Hourly DVOL candles from DVOL_START_MS to now, chunked 30d. -> list of
    iv_store.append_dvol-style dicts [{currency, ts, open, high, low, close}]."""
    end = _now_ms()
    rows: list[dict] = []
    cur = DVOL_START_MS
    while cur < end:
        nxt = min(cur + DVOL_CHUNK_MS, end)
        j = _get(DERIBIT, "/get_volatility_index_data",
                 {"currency": currency, "resolution": "3600",
                  "start_timestamp": cur, "end_timestamp": nxt}, session)
        data = (j.get("result") or {}).get("data") or []
        for candle in data:
            try:
                ts, o, h, l, c = (int(candle[0]), float(candle[1]), float(candle[2]),
                                  float(candle[3]), float(candle[4]))
            except (TypeError, ValueError, IndexError):
                continue
            rows.append({"currency": currency, "ts": ts, "open": o, "high": h,
                         "low": l, "close": c})
        cur = nxt
    return rows


def compute_realized_vol(closes: list[tuple[int, float]],
                         window_days: int = REALIZED_WINDOW_DAYS) -> list[dict]:
    """Annualized realized vol (std of daily log-returns x sqrt(365)) over a
    trailing window, per day."""
    closes = sorted(closes)
    vals = [c for _, c in closes if c is not None and c > 0]
    days = [d for d, c in closes if c is not None and c > 0]
    out: list[dict] = []
    if len(vals) < 3:
        return out
    for i in range(len(vals)):
        lo = max(0, i - window_days)
        window = vals[lo:i + 1]
        if len(window) < 3:
            rv = None
        else:
            lr = [math.log(window[j] / window[j - 1]) for j in range(1, len(window))]
            lr = [x for x in lr if math.isfinite(x)]
            if len(lr) < 2:
                rv = None
            else:
                mean = sum(lr) / len(lr)
                var = sum((x - mean) ** 2 for x in lr) / (len(lr) - 1)
                rv = math.sqrt(var) * math.sqrt(DAYS_PER_YEAR)
        out.append({"day": days[i], "realized_vol": rv})
    return out


def daily_dvol_close(currency: str) -> dict[int, float]:
    """Map day (ms) -> DVOL close (last hourly candle of the UTC day), from the
    (already backfilled) iv_store.dvol_index."""
    df = iv_store.read_dvol(currency)
    if df.empty or "close" not in df.columns:
        return {}
    by_day: dict[int, list] = collections.defaultdict(list)
    for ts, c in zip(df["ts"], df["close"]):
        try:
            by_day[_day_of(int(ts))].append((int(ts), float(c)))
        except (TypeError, ValueError):
            continue
    out: dict[int, float] = {}
    for day, items in by_day.items():
        out[day] = max(items, key=lambda x: x[0])[1]
    return out


def _fetch_process_day(args: tuple) -> tuple[int, list[dict], list[dict]]:
    """Worker: fetch + reconstruct a single day (own session per thread)."""
    currency, day, inst_map = args
    s = requests.Session()
    try:
        trades = fetch_day_trades(currency, day, s)
        urows, srows = process_day(currency, day, trades, inst_map)
        return day, urows, srows
    finally:
        s.close()


def ingest_currency(currency: str, periods: tuple[str, ...], years: float,
                    limit_days: int | None, dry_run: bool,
                    session: requests.Session) -> dict:
    conn = oh.open_store() if not dry_run else None
    try:
        now = _now_ms()
        start_cut = now - int(years * 365.25 * MS_PER_DAY)
        inst_map = build_inst_map(currency, periods, start_cut, session)

        done = oh.done_days(conn, currency) if conn else set()
        day_cursor = max(_day_of(start_cut), 0)
        end_cursor = _day_of(now)
        todo: list[int] = []
        d = day_cursor
        while d <= end_cursor:
            if d not in done:
                todo.append(d)
            d += MS_PER_DAY
        if limit_days is not None:
            todo = todo[:limit_days]

        n_strad = n_under = 0
        if not dry_run and todo:
            assert conn is not None
            work = [(currency, day, inst_map) for day in todo]
            with ThreadPoolExecutor(max_workers=WORKERS) as ex:
                futs = [ex.submit(_fetch_process_day, w) for w in work]
                for fut in as_completed(futs):
                    day, urows, srows = fut.result()
                    oh.append_underlying(conn, urows)
                    oh.append_atm_straddle(conn, srows)
                    oh.mark_day_done(conn, currency, day)
                    n_under += len(urows)
                    n_strad += len(srows)
        elif dry_run:
            for day in todo:
                trades = fetch_day_trades(currency, day, session)
                _, srows = process_day(currency, day, trades, inst_map)
                n_strad += len(srows)
                n_under += 1
        return {"currency": currency, "instruments": len(inst_map),
                "days": len(todo), "underlying_rows": n_under,
                "straddle_rows": n_strad}
    finally:
        if conn:
            conn.close()


def run_dvol(currency: str, session: requests.Session) -> int:
    conn = iv_store.open_store()
    try:
        rows = fetch_dvol_all(currency, session)
        if not rows:
            return 0
        new = iv_store.append_dvol(conn, rows)
        iso = datetime.now(timezone.utc).isoformat()
        iv_store.upsert_state(conn, "dvol", currency, max(r["ts"] for r in rows), iso)
        return new
    finally:
        conn.close()


def finalize_realized(currency: str) -> int:
    """Compute realized-vol daily from underlying_daily + join DVOL close."""
    conn = oh.open_store()
    try:
        rows = conn.execute(
            "SELECT day, close FROM underlying_daily WHERE currency=? "
            "ORDER BY day ASC", (currency,)).fetchall()
        if not rows:
            return 0
        rv_rows = compute_realized_vol(rows)
        dvol_by_day = daily_dvol_close(currency)
        out = [{"currency": currency, "day": r["day"],
                "realized_vol": r["realized_vol"],
                "dvol": dvol_by_day.get(r["day"])} for r in rv_rows]
        return oh.append_realized_vol(conn, out)
    finally:
        conn.close()


def report(currency: str) -> dict:
    conn = oh.open_store()
    try:
        s = oh.coverage(conn, "options_atm_straddle", currency)
        u = oh.coverage(conn, "underlying_daily", currency)
        r = oh.coverage(conn, "realized_vol_daily", currency)
        return {"straddle": s, "underlying": u, "realized_vol": r}
    finally:
        conn.close()


def _fmt(c: dict) -> str:
    if c["n"] == 0:
        return "n=0"
    lo = datetime.fromtimestamp(c["min"] / 1000, tz=timezone.utc).date()
    hi = datetime.fromtimestamp(c["max"] / 1000, tz=timezone.utc).date()
    return f"n={c['n']} [{lo} .. {hi}]"


def main() -> int:
    ap = argparse.ArgumentParser(description="US-231 Deribit options-history backfill")
    ap.add_argument("--currency", nargs="*", default=list(CURRENCIES))
    ap.add_argument("--years", type=float, default=2.0)
    ap.add_argument("--periods", nargs="*", default=list(DEFAULT_PERIODS))
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--skip-dvol", action="store_true")
    ap.add_argument("--skip-realized", action="store_true")
    ap.add_argument("--limit-days", type=int, default=None)
    args = ap.parse_args()

    session = requests.Session()
    periods = tuple(args.periods)
    print(f"[US-231] backfill start {datetime.now(timezone.utc).isoformat()}")
    print(f"  currencies={args.currency} years={args.years} periods={periods} "
          f"dry={args.dry_run}")

    for currency in args.currency:
        res = ingest_currency(currency, periods, args.years,
                              args.limit_days, args.dry_run, session)
        if args.dry_run:
            print(f"[{currency}] DRY-RUN: instruments={res['instruments']} "
                  f"days={res['days']}")
            continue
        print(f"[{currency}] straddle+underlying: instruments={res['instruments']} "
              f"days={res['days']} underlying_rows={res['underlying_rows']} "
              f"straddle_rows={res['straddle_rows']}")

        if not args.skip_dvol:
            try:
                new_dvol = run_dvol(currency, session)
                print(f"[{currency}] DVOL backfill: new={new_dvol}")
            except Exception as e:  # noqa: BLE001
                print(f"[{currency}] DVOL backfill FAILED: {e}")

        if not args.skip_realized:
            try:
                new_rv = finalize_realized(currency)
                print(f"[{currency}] realized-vol rows: new={new_rv}")
            except Exception as e:  # noqa: BLE001
                print(f"[{currency}] realized-vol FAILED: {e}")

        rep = report(currency)
        print(f"[{currency}] COVERAGE  straddle={_fmt(rep['straddle'])} | "
              f"underlying={_fmt(rep['underlying'])} | "
              f"realized_vol={_fmt(rep['realized_vol'])}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
