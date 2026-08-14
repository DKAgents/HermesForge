#!/usr/bin/env python3
"""
fetch_earnings_calendar.py — Upcoming earnings calendar data feed

Returns a list of upcoming earnings releases with date, ticker, EPS estimate,
revenue estimate, and whether the report is after market close.

Provider cascade (tried in order; each falls back gracefully on failure):
  1. Finnhub free-tier API  (https://finnhub.io/api/v1/calendar/earnings)
       - Requires an API key.  Reads FINNHUB_API_KEY from the environment.
       - Without a key Finnhub returns HTTP 401 — we note that and fall through.
       - A free Finnhub key (https://finnhub.io/register) enables bulk fetching
         of the entire earnings calendar in a single call, which is far faster
         than the per-ticker yfinance fallback for the full 529-stock universe.
  2. Nasdaq public earnings-calendar API
       (https://api.nasdaq.com/api/calendar/earnings?date=YYYY-MM-DD)
       - Free, no key, no auth.  Returns all earnings for a given calendar date
         with symbol, company name, EPS forecast, fiscal quarter, and time slot
         (pre-market / after-hours / not-supplied).
       - Queried per-day for each day in the requested window.
       - Does NOT include revenue estimates.
  3. Financial Modeling Prep free tier
       (https://financialmodelingprep.com/api/v3/earning_calendar?from=..&to=..)
       - Requires a free API key (FMP_API_KEY).  Without a key returns 401.
       - Includes EPS estimate and revenue estimate.  A free signup at
         https://site.financialmodelingprep.com/register would enable this path.
  4. yfinance per-ticker fallback
       - yf.Ticker(ticker).calendar returns a dict with 'Earnings Date' (a list
         of date strings), 'Earnings Average', 'Earnings High', 'Earnings Low',
         'Revenue Average', 'Revenue High', 'Revenue Low'.
       - Works without any key but is slow (one HTTP call per ticker), so it is
         best used for a small watch list or current open positions rather than
         the full 529-stock universe.

Each earnings dict:
    {
        "date":             "2026-08-26",     # YYYY-MM-DD
        "ticker":           "NVDA",
        "name":             "NVIDIA Corporation",
        "eps_estimate":     2.08,             # consensus EPS forecast (float or None)
        "revenue_estimate": 91846098240,      # consensus revenue (float or None)
        "is_after_close":   True,             # True = after-hours, False = pre-market, None = unknown
        "fiscal_quarter":   "Q2 2026",        # fiscal quarter ending (best-effort)
        "source":           "nasdaq",         # provider tag
    }

Caches to ~/.hermes/market_data/earnings_calendar/ as dated JSON files.

Public API:
    get_earnings_calendar(days_ahead=7, tickers=None) -> list[dict]
    get_earnings_for_ticker(ticker) -> dict | None
    get_earnings_this_week() -> list[dict]

Usage:
    python3 fetch_earnings_calendar.py                       # next 7 days
    python3 fetch_earnings_calendar.py --days 14             # next 14 days
    python3 fetch_earnings_calendar.py --tickers AAPL NVDA TSLA MSFT AMZN
    python3 fetch_earnings_calendar.py --force               # force refresh
"""

from __future__ import annotations

import json
import os
import pathlib
import sys
import argparse
import time
from datetime import datetime, timedelta, timezone

import requests

# Make the sibling validation package importable when run as a script.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

try:
    from validation.universe import get_universe  # noqa: E402
except Exception:  # pragma: no cover
    get_universe = None  # type: ignore[assignment]

# Optional yfinance (per-ticker fallback).
try:
    import yfinance as yf
except Exception:  # pragma: no cover
    yf = None  # type: ignore[assignment]

# --------------------------------------------------------------------------- #
# Config
# --------------------------------------------------------------------------- #

CACHE_DIR = pathlib.Path.home() / ".hermes" / "market_data" / "earnings_calendar"
CACHE_MAX_AGE_HOURS = 12          # earnings dates are stable; refresh 2x/day is plenty
REQUEST_TIMEOUT = 25              # seconds
YF_DELAY = 0.20                   # be polite to Yahoo

HTTP_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
}

# Nasdaq API time-slot -> is_after_close mapping
_NASDAQ_TIME_MAP = {
    "time-after-hours": True,    # reports after market close
    "time-pre-market": False,    # reports before market open
    "time-not-supplied": None,   # time not disclosed
    "time-tba": None,
    "": None,
}


# --------------------------------------------------------------------------- #
# Small helpers
# --------------------------------------------------------------------------- #

def _to_float(v, default=None):
    """Parse a value to float, stripping $, commas, parentheses (negatives)."""
    if v is None:
        return default
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip()
    if not s or s.upper() in ("N/A", "NA", "-"):
        return default
    negative = False
    if s.startswith("(") and s.endswith(")"):
        negative = True
        s = s[1:-1]
    s = s.replace("$", "").replace(",", "").replace("%", "").strip()
    if not s:
        return default
    try:
        f = float(s)
        return -f if negative else f
    except (TypeError, ValueError):
        return default


def _clean_ticker(tk: str) -> str:
    return tk.upper().strip().replace("-", "-") if tk else ""


# --------------------------------------------------------------------------- #
# Cache helpers
# --------------------------------------------------------------------------- #

def _cache_path(day: datetime) -> pathlib.Path:
    return CACHE_DIR / f"earnings_calendar_{day.strftime('%Y-%m-%d')}.json"


def _read_cache(day: datetime, max_age_hours: float = CACHE_MAX_AGE_HOURS):
    """Return cached earnings for `day` if fresh enough, else None."""
    path = _cache_path(day)
    if not path.exists():
        return None
    try:
        mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
        age_h = (datetime.now(timezone.utc) - mtime).total_seconds() / 3600.0
        if age_h > max_age_hours:
            return None
        with path.open() as fh:
            payload = json.load(fh)
        return payload.get("earnings", [])
    except Exception:
        return None


def _write_cache(earnings: list, day: datetime) -> None:
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        path = _cache_path(day)
        with path.open("w") as fh:
            json.dump(
                {
                    "fetched_at": datetime.now(timezone.utc).isoformat(),
                    "query_date": day.strftime("%Y-%m-%d"),
                    "count": len(earnings),
                    "earnings": earnings,
                },
                fh,
                indent=2,
            )
    except Exception as exc:  # pragma: no cover - cache must never be fatal
        print(f"[earnings_calendar] cache write failed: {exc}", file=sys.stderr)


# --------------------------------------------------------------------------- #
# Provider 1 — Finnhub (needs API key)
# --------------------------------------------------------------------------- #

def _fetch_finnhub(start: datetime, end: datetime, tickers: list[str] | None) -> list[dict] | None:
    """
    Fetch from Finnhub free-tier earnings calendar.
    Returns list of normalised earnings dicts, or None if unavailable (no key /
    blocked / error).  Errors are logged to stderr but never raised.
    """
    key = os.environ.get("FINNHUB_API_KEY", "").strip()
    if not key:
        # Also check .env file in project root
        env_path = pathlib.Path(__file__).resolve().parent.parent.parent / ".env"
        if env_path.exists():
            key = _read_env_var(env_path, "FINNHUB_API_KEY")
    if not key:
        print("[earnings_calendar] Finnhub: no FINNHUB_API_KEY in env — skipping "
              "(free tier requires a key; register at https://finnhub.io/register).",
              file=sys.stderr)
        return None

    url = "https://finnhub.io/api/v1/calendar/earnings"
    params = {
        "from": start.strftime("%Y-%m-%d"),
        "to": end.strftime("%Y-%m-%d"),
        "token": key,
    }
    try:
        resp = requests.get(url, params=params, headers=HTTP_HEADERS,
                            timeout=REQUEST_TIMEOUT)
        if resp.status_code == 401:
            print("[earnings_calendar] Finnhub: API key rejected (401).",
                  file=sys.stderr)
            return None
        resp.raise_for_status()
        raw = resp.json().get("earningsCalendar", []) or resp.json().get("data", [])
    except Exception as exc:
        print(f"[earnings_calendar] Finnhub fetch failed: {exc}", file=sys.stderr)
        return None

    ticker_set = set(tickers) if tickers else None
    out = []
    for item in raw:
        try:
            tk = (item.get("symbol") or item.get("ticker") or "").upper()
            if not tk or (ticker_set and tk not in ticker_set):
                continue
            ed = item.get("date", "")
            is_after = None
            when = (item.get("hour") or item.get("time") or "").lower()
            if when in ("amc", "after_close", "after-hours"):
                is_after = True
            elif when in ("bmo", "before_open", "pre-market"):
                is_after = False
            elif when == "dmh":
                is_after = None
            eps = _to_float(item.get("epsEstimate") or item.get("eps") or
                            item.get("epsActual"))
            rev = _to_float(item.get("revenueEstimate") or item.get("revenue"))
            out.append({
                "date": ed,
                "ticker": tk,
                "name": item.get("name", ""),
                "eps_estimate": eps,
                "revenue_estimate": rev,
                "is_after_close": is_after,
                "fiscal_quarter": item.get("fiscalQuarter", ""),
                "source": "finnhub",
            })
        except Exception:
            continue
    return out


def _read_env_var(env_path: pathlib.Path, var_name: str) -> str:
    """Read a single variable from a .env file (KEY=value lines)."""
    try:
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                k, v = line.split("=", 1)
                if k.strip() == var_name:
                    return v.strip().strip("'\"")
    except Exception:
        pass
    return ""


# --------------------------------------------------------------------------- #
# Provider 2 — Nasdaq public earnings-calendar API (free, no key)
# --------------------------------------------------------------------------- #

NASDAQ_API = "https://api.nasdaq.com/api/calendar/earnings"


def _fetch_nasdaq_day(day: datetime, tickers: list[str] | None) -> list[dict]:
    """
    Fetch one day's earnings from the Nasdaq public calendar API.
    Returns a list of normalised dicts (possibly empty).  Never raises.
    """
    date_str = day.strftime("%Y-%m-%d")
    params = {"date": date_str}
    # Nasdaq API can be picky about headers — include a referer.
    headers = {
        **HTTP_HEADERS,
        "Referer": "https://www.nasdaq.com/earnings/earnings-calendar.aspx",
    }
    try:
        resp = requests.get(NASDAQ_API, params=params, headers=headers,
                            timeout=REQUEST_TIMEOUT)
        if resp.status_code != 200:
            print(f"[earnings_calendar] Nasdaq API {date_str} -> HTTP "
                  f"{resp.status_code}", file=sys.stderr)
            return []
        body = resp.json()
    except Exception as exc:
        print(f"[earnings_calendar] Nasdaq API {date_str} failed: {exc}",
              file=sys.stderr)
        return []

    rows = []
    try:
        rows = body.get("data", {}).get("rows", []) or []
    except Exception:
        rows = []

    ticker_set = set(tickers) if tickers else None
    out = []
    for row in rows:
        try:
            tk = (row.get("symbol") or "").upper().strip()
            if not tk or (ticker_set and tk not in ticker_set):
                continue
            eps = _to_float(row.get("epsForecast"))
            time_slot = row.get("time", "")
            is_after = _NASDAQ_TIME_MAP.get(time_slot, None)
            fiscal = row.get("fiscalQuarterEnding", "")
            out.append({
                "date": date_str,
                "ticker": tk,
                "name": row.get("name", ""),
                "eps_estimate": eps,
                "revenue_estimate": None,  # Nasdaq API does not provide revenue
                "is_after_close": is_after,
                "fiscal_quarter": fiscal,
                "source": "nasdaq",
            })
        except Exception:
            continue
    return out


def _fetch_nasdaq(start: datetime, end: datetime, tickers: list[str] | None) -> list[dict]:
    """
    Fetch the full earnings calendar from the Nasdaq public API by querying
    each day in the [start, end] window.  Returns a merged, de-duplicated list.
    """
    merged: list[dict] = []
    day = start
    while day.date() <= end.date():
        rows = _fetch_nasdaq_day(day, tickers)
        merged.extend(rows)
        # Small delay to be polite across multi-day queries.
        if day != end:
            time.sleep(0.15)
        day += timedelta(days=1)
    return merged


# --------------------------------------------------------------------------- #
# Provider 3 — Financial Modeling Prep (needs free key)
# --------------------------------------------------------------------------- #

def _fetch_fmp(start: datetime, end: datetime, tickers: list[str] | None) -> list[dict] | None:
    """
    Fetch from Financial Modeling Prep earning_calendar endpoint.
    Requires FMP_API_KEY (free signup at https://site.financialmodelingprep.com/register).
    Returns normalised list or None if no key / blocked.
    """
    key = os.environ.get("FMP_API_KEY", "").strip()
    if not key:
        env_path = pathlib.Path(__file__).resolve().parent.parent.parent / ".env"
        if env_path.exists():
            key = _read_env_var(env_path, "FMP_API_KEY")
    if not key:
        print("[earnings_calendar] FMP: no FMP_API_KEY in env — skipping "
              "(free signup at https://site.financialmodelingprep.com/register "
              "enables bulk EPS+revenue estimates).", file=sys.stderr)
        return None

    url = "https://financialmodelingprep.com/api/v3/earning_calendar"
    params = {
        "from": start.strftime("%Y-%m-%d"),
        "to": end.strftime("%Y-%m-%d"),
        "apikey": key,
    }
    try:
        resp = requests.get(url, params=params, headers=HTTP_HEADERS,
                            timeout=REQUEST_TIMEOUT)
        if resp.status_code == 401:
            print("[earnings_calendar] FMP: API key rejected (401).",
                  file=sys.stderr)
            return None
        resp.raise_for_status()
        raw = resp.json()
        if isinstance(raw, dict) and raw.get("Error Message"):
            print(f"[earnings_calendar] FMP error: {raw['Error Message']}",
                  file=sys.stderr)
            return None
        if not isinstance(raw, list):
            raw = raw.get("earningsCalendar", []) if isinstance(raw, dict) else []
    except Exception as exc:
        print(f"[earnings_calendar] FMP fetch failed: {exc}", file=sys.stderr)
        return None

    ticker_set = set(tickers) if tickers else None
    out = []
    for item in raw:
        try:
            tk = (item.get("symbol") or "").upper().strip()
            if not tk or (ticker_set and tk not in ticker_set):
                continue
            ed = item.get("date", "")[:10]
            eps = _to_float(item.get("epsActual") or item.get("epsEstimate"))
            rev = _to_float(item.get("revenueActual") or item.get("revenueEstimate"))
            out.append({
                "date": ed,
                "ticker": tk,
                "name": "",
                "eps_estimate": eps,
                "revenue_estimate": rev,
                "is_after_close": None,
                "fiscal_quarter": "",
                "source": "fmp",
            })
        except Exception:
            continue
    return out


# --------------------------------------------------------------------------- #
# Provider 4 — yfinance per-ticker fallback
# --------------------------------------------------------------------------- #

def _fetch_yfinance(tickers: list[str], days_ahead: int) -> list[dict]:
    """
    Fetch earnings dates via yfinance `Ticker.calendar` for each ticker.
    Returns a list of normalised dicts.  Slow (one call per ticker) but
    works without any API key.
    """
    if yf is None:
        print("[earnings_calendar] yfinance not installed; cannot use fallback.",
              file=sys.stderr)
        return []

    horizon_end = datetime.now() + timedelta(days=days_ahead)
    out = []
    for i, tk in enumerate(tickers):
        try:
            cal = yf.Ticker(tk).calendar
        except Exception as exc:
            print(f"[earnings_calendar] yfinance error for {tk}: {exc!r}",
                  file=sys.stderr)
            continue
        if not cal or not isinstance(cal, dict):
            continue
        ed_raw = cal.get("Earnings Date")
        if not ed_raw:
            continue
        # ed_raw can be a list of date strings or a single string.
        if isinstance(ed_raw, str):
            ed_raw = [ed_raw]
        eps_avg = _to_float(cal.get("Earnings Average"))
        eps_high = _to_float(cal.get("Earnings High"))
        eps_low = _to_float(cal.get("Earnings Low"))
        rev_avg = _to_float(cal.get("Revenue Average"))
        rev_high = _to_float(cal.get("Revenue High"))
        rev_low = _to_float(cal.get("Revenue Low"))
        for ed in ed_raw:
            ed_str = str(ed)[:10] if ed else ""
            if not ed_str:
                continue
            try:
                ed_dt = datetime.fromisoformat(ed_str)
            except Exception:
                continue
            # Only include dates within our forward window.
            if ed_dt.date() < datetime.now().date():
                continue
            if ed_dt.date() > horizon_end.date():
                continue
            out.append({
                "date": ed_str,
                "ticker": tk,
                "name": "",
                "eps_estimate": eps_avg,
                "revenue_estimate": rev_avg,
                "is_after_close": None,  # yfinance calendar does not expose time slot
                "fiscal_quarter": "",
                "source": "yfinance",
            })
        if (i + 1) % 25 == 0:
            print(f"[earnings_calendar] yfinance progress {i+1}/{len(tickers)}",
                  file=sys.stderr)
        time.sleep(YF_DELAY)
    return out


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #

def _in_window(ev: dict, start: datetime, end: datetime) -> bool:
    """Keep earnings whose date falls within [start, end] inclusive."""
    d = (ev.get("date") or "").strip()
    if not d:
        return False
    try:
        ed = datetime.fromisoformat(d).replace(tzinfo=None)
    except Exception:
        try:
            ed = datetime.strptime(d, "%Y-%m-%d")
        except Exception:
            return False
    return start.date() <= ed.date() <= end.date()


def _dedup(events: list[dict]) -> list[dict]:
    seen = set()
    out = []
    for e in events:
        key = (e.get("date"), e.get("ticker"))
        if key in seen:
            continue
        seen.add(key)
        out.append(e)
    return out


def _fetch_all(start: datetime, end: datetime, tickers: list[str] | None) -> list[dict]:
    """
    Run the provider cascade and return the best available earnings list.

    The cascade order depends on whether specific tickers were provided:

    Bulk mode (tickers=None — full calendar, no per-ticker filter):
      1. Finnhub  (key-gated, single bulk call — fastest for full universe)
      2. Nasdaq   (free, no key, per-day — primary working source)
      3. FMP      (free key, bulk, includes revenue)
      4. yfinance (free, no key, per-ticker — very slow for 529 stocks)

    Ticker-filtered mode (a small list of tickers is provided):
      1. Finnhub  (key-gated, single bulk call, filtered client-side)
      2. yfinance (free, per-ticker — fast for small lists, covers any date
                   range, includes revenue estimates)
      3. Nasdaq   (free, per-day — slow for long windows; used only if
                   yfinance returns nothing)
      4. FMP      (free key, bulk, includes revenue)

    Rationale: the Nasdaq API is queried per calendar day, so a 90-day window
    requires 90 HTTP calls.  For a 5-ticker watch list, yfinance needs only 5
    calls regardless of the window length.  We therefore prefer yfinance when
    a small ticker set is given, and prefer Nasdaq for bulk fetches.
    """
    sources_tried: list[str] = []
    window_days = (end - start).days

    # 1. Finnhub (key-gated, bulk — always first because it's one call)
    ev = _fetch_finnhub(start, end, tickers)
    if ev:
        return _dedup(ev)
    sources_tried.append("finnhub: skipped/failed")

    if tickers and len(tickers) <= 60:
        # Ticker-filtered mode: yfinance is faster than per-day Nasdaq.
        # 2. yfinance
        ev = _fetch_yfinance(tickers, days_ahead=window_days)
        if ev:
            return _dedup(ev)
        sources_tried.append("yfinance: empty")

        # 3. Nasdaq (per-day fallback — cap to avoid excessive calls)
        nasdaq_end = end
        if window_days > 30:
            nasdaq_end = start + timedelta(days=30)
            print(f"[earnings_calendar] Nasdaq fallback: capping window to 30 days "
                  f"(yfinance returned nothing for {len(tickers)} tickers).",
                  file=sys.stderr)
        ev = _fetch_nasdaq(start, nasdaq_end, tickers)
        if ev:
            return _dedup(ev)
        sources_tried.append("nasdaq: empty")

        # 4. FMP (free key)
        ev = _fetch_fmp(start, end, tickers)
        if ev:
            return _dedup(ev)
        sources_tried.append("fmp: skipped/failed")
    else:
        # Bulk mode: Nasdaq (per-day) is the primary free source.
        # 2. Nasdaq
        ev = _fetch_nasdaq(start, end, tickers)
        if ev:
            return _dedup(ev)
        sources_tried.append("nasdaq: empty")

        # 3. FMP (free key)
        ev = _fetch_fmp(start, end, tickers)
        if ev:
            return _dedup(ev)
        sources_tried.append("fmp: skipped/failed")

        # 4. yfinance per-ticker fallback (slow for full universe)
        if tickers:
            ev = _fetch_yfinance(tickers, days_ahead=window_days)
            if ev:
                return _dedup(ev)
            sources_tried.append("yfinance: empty")
        else:
            # No ticker list — load the universe if available.
            if get_universe is not None:
                try:
                    uni = list(get_universe())
                    ev = _fetch_yfinance(uni, days_ahead=window_days)
                    if ev:
                        return _dedup(ev)
                    sources_tried.append("yfinance(universe): empty")
                except Exception as exc:
                    sources_tried.append(f"yfinance(universe): {exc!r}")
            else:
                sources_tried.append("yfinance: no universe available")

    print(f"[earnings_calendar] WARNING: no provider returned data. "
          f"Sources tried: {'; '.join(sources_tried)}", file=sys.stderr)
    return []


def get_earnings_calendar(days_ahead: int = 7, tickers=None, force: bool = False) -> list[dict]:
    """
    Return upcoming earnings releases for the next `days_ahead` days.

    If `tickers` is provided (a list of ticker strings), results are filtered
    to only those tickers.  If `tickers` is None, all earnings in the window
    are returned (bulk fetch via Nasdaq/Finnhub; yfinance fallback loads the
    full HermesForge universe — slow).

    Results are cached per-query-date as dated JSON files in
    ~/.hermes/market_data/earnings_calendar/ and refreshed at most every
    CACHE_MAX_AGE_HOURS (unless force=True).

    Args:
        days_ahead: number of days forward from today (default 7).
        tickers:    optional list of ticker strings to filter to.
        force:      bypass cache and re-fetch.

    Returns:
        list of earnings dicts (see module docstring for schema), sorted by
        date then ticker.
    """
    if days_ahead < 1:
        days_ahead = 1

    now = datetime.now()
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=days_ahead)

    # Normalise tickers
    ticker_list = None
    if tickers:
        ticker_list = [_clean_ticker(t) for t in tickers if t and t.strip()]
        ticker_list = list(dict.fromkeys(ticker_list))  # dedup, preserve order

    # Try cache (covers today's query date).
    if not force:
        cached = _read_cache(now, max_age_hours=CACHE_MAX_AGE_HOURS)
        if cached is not None:
            windowed = [e for e in cached if _in_window(e, start, end)]
            if ticker_list:
                tset = set(ticker_list)
                windowed = [e for e in windowed if e.get("ticker") in tset]
            if windowed:
                print(f"[earnings_calendar] using cache ({len(windowed)} earnings "
                      f"in window).", file=sys.stderr)
                return _sort_earnings(windowed)

    earnings = _fetch_all(start, end, ticker_list)
    windowed = [e for e in earnings if _in_window(e, start, end)]

    # Cache the full fetched set (so future queries with different ticker
    # filters or larger windows can reuse).
    if earnings:
        _write_cache(earnings, now)

    return _sort_earnings(windowed)


def _sort_earnings(events: list[dict]) -> list[dict]:
    """Sort by date, then is_after_close (pre-market before after-hours), then ticker."""
    def sort_key(e):
        is_after = e.get("is_after_close")
        # None sorts in the middle; False (pre-market) first, True (after-hours) last
        if is_after is None:
            slot = 1
        elif is_after:
            slot = 2
        else:
            slot = 0
        return (e.get("date", ""), slot, e.get("ticker", ""))
    events.sort(key=sort_key)
    return events


def get_earnings_for_ticker(ticker: str, days_ahead: int = 90, force: bool = False) -> dict | None:
    """
    Return the next upcoming earnings release for a specific ticker, or None
    if none found within the look-ahead window.

    Uses the same provider cascade.  For a single ticker this is fast even with
    the yfinance fallback.

    Args:
        ticker:     stock ticker symbol (e.g. "AAPL").
        days_ahead: how far forward to look (default 90 days).
        force:      bypass cache.

    Returns:
        A single earnings dict (see module docstring) or None.
    """
    tk = _clean_ticker(ticker)
    if not tk:
        return None
    earnings = get_earnings_calendar(days_ahead=days_ahead, tickers=[tk], force=force)
    if earnings:
        return earnings[0]
    return None


def get_earnings_this_week(force: bool = False) -> list[dict]:
    """
    Return all earnings releases scheduled for the current calendar week
    (Monday through Sunday).  Uses the same provider cascade and cache.

    Args:
        force: bypass cache.

    Returns:
        list of earnings dicts (see module docstring), sorted by date.
    """
    now = datetime.now()
    # Monday = 0
    monday = now - timedelta(days=now.weekday())
    monday = monday.replace(hour=0, minute=0, second=0, microsecond=0)
    sunday = monday + timedelta(days=6)
    days_to_sunday = (sunday - now).days + 1
    if days_to_sunday < 1:
        days_to_sunday = 1
    return get_earnings_calendar(days_ahead=days_to_sunday, force=force)


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def _print_earnings(earnings: list[dict], title: str) -> None:
    print(f"\n{title} — {len(earnings)} earnings")
    print("-" * 100)
    if not earnings:
        print("  (none)")
        return
    hdr = (f"{'Date':<12}{'Ticker':<8}{'When':<14}{'EPS Est':<10}"
           f"{'Revenue Est':<16}{'Fiscal Qtr':<14}{'Company'}")
    print(hdr)
    print("-" * 100)
    for e in earnings:
        when = e.get("is_after_close")
        when_str = "after-close" if when is True else ("pre-market" if when is False else "unknown")
        eps = e.get("eps_estimate")
        eps_str = f"${eps:.2f}" if eps is not None else ""
        rev = e.get("revenue_estimate")
        if rev is not None:
            if rev >= 1e9:
                rev_str = f"${rev/1e9:.2f}B"
            elif rev >= 1e6:
                rev_str = f"${rev/1e6:.1f}M"
            else:
                rev_str = f"${rev:,.0f}"
        else:
            rev_str = ""
        print(f"{e.get('date',''):<12}"
              f"{e.get('ticker',''):<8}"
              f"{when_str:<14}"
              f"{eps_str:<10}"
              f"{rev_str:<16}"
              f"{(e.get('fiscal_quarter') or ''):<14}"
              f"{e.get('name','')[:30]}")
    srcs = sorted({e.get("source", "?") for e in earnings})
    print(f"\nsource(s): {', '.join(srcs)}")


def _build_argparser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fetch upcoming earnings calendar")
    ap.add_argument("--days", type=int, default=7,
                    help="Days ahead to look (default 7)")
    ap.add_argument("--tickers", nargs="*", default=None,
                    metavar="TKR",
                    help="Filter to specific tickers (e.g. --tickers AAPL NVDA TSLA)")
    ap.add_argument("--force", action="store_true",
                    help="Force refresh cache")
    ap.add_argument("--this-week", action="store_true",
                    help="Show earnings for the current calendar week")
    ap.add_argument("--ticker", default=None,
                    help="Get next earnings date for a single ticker")
    return ap


def main(argv: list[str] | None = None) -> int:
    ap = _build_argparser()
    args = ap.parse_args(argv)

    if args.ticker:
        ev = get_earnings_for_ticker(args.ticker, force=args.force)
        if ev:
            _print_earnings([ev], f"Next earnings for {args.ticker.upper()}")
        else:
            print(f"\nNo upcoming earnings found for {args.ticker.upper()}")
        return 0

    if args.this_week:
        earnings = get_earnings_this_week(force=args.force)
        _print_earnings(earnings, "Earnings this week")
        return 0

    earnings = get_earnings_calendar(
        days_ahead=args.days,
        tickers=args.tickers,
        force=args.force,
    )
    _print_earnings(earnings, f"Earnings calendar (next {args.days}d)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
