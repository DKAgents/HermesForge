#!/usr/bin/env python3
"""
fetch_economic_calendar.py — Upcoming economic-event calendar feed

Returns a list of upcoming economic events (CPI, FOMC, NFP, GDP, PPI,
retail sales, jobless claims, etc.) with date, time, country, event name,
importance (high/medium/low), actual, previous, and consensus.

Provider cascade (tried in order):
  1. Finnhub free-tier API  (https://finnhub.io/api/v1/calendar/economic)
       - Requires an API key.  Reads FINNHUB_API_KEY from the environment.
       - Without a key Finnhub returns HTTP 401 — we note that and fall through.
  2. Trading Economics API  (https://api.tradingeconomics.com/calendar)
       - Requires client + key.  Reads TRADINGECONOMICS_CLIENT / _KEY from env.
       - Without credentials we note that and fall through.
  3. Forex Factory public JSON feed  (https://nfs.faireconomy.media)
       - Free, no key, no auth, returns exactly the fields we need.
       - Provides the current calendar week (Sat->Fri) plus, when published
         (typically late Fri/Sat), the following week.
  4. HTML scrape fallback (Forex Factory / Investing.com / Nasdaq)
       - Best-effort.  These pages sit behind Cloudflare bot-protection and
         usually return HTTP 403 to non-browser clients, so this is a
         last-ditch attempt that is expected to fail in most environments.

Caches to ~/.hermes/market_data/economic_calendar/ as dated JSON files.

Public API:
    get_economic_calendar(days_ahead=7) -> list[dict]
    get_next_high_impact_events(days_ahead=7) -> list[dict]

Each event dict:
    {
        "date":      "2026-08-14",          # YYYY-MM-DD
        "time":      "08:30",              # HH:MM (24h, event local tz) or ""
        "datetime":  "2026-08-14T08:30:00-04:00",  # ISO 8601 w/ tz (or "")
        "country":   "USD",                # ISO currency / country code
        "event":     "Core CPI m/m",        # event name
        "importance":"high",               # high / medium / low / holiday
        "actual":    "",                   # "" until released
        "previous":  "0.3%",
        "consensus": "0.2%",               # "" if none
        "source":    "forexfactory",        # provider tag
    }

Usage:
    python3 fetch_economic_calendar.py                # print upcoming events
    python3 fetch_economic_calendar.py --days 14      # next 14 days
    python3 fetch_economic_calendar.py --high-impact  # high impact only
    python3 fetch_economic_calendar.py --force        # force refresh cache
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

# --------------------------------------------------------------------------- #
# Config
# --------------------------------------------------------------------------- #

CACHE_DIR = pathlib.Path.home() / ".hermes" / "market_data" / "economic_calendar"
CACHE_MAX_AGE_HOURS = 6          # re-fetch at most every 6h
REQUEST_TIMEOUT = 25             # seconds
HTTP_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
}

# Normalise various "importance" vocabularies to {high, medium, low, holiday}.
_IMPORTANCE_MAP = {
    "high": "high", "3": "high", "bullish": "high", "red": "high",
    "medium": "medium", "2": "medium", "orange": "medium", "medium impact": "medium",
    "low": "low", "1": "low", "low impact": "low", "yellow": "low", "white": "low",
    "holiday": "holiday", "non-economic": "holiday", "0": "holiday",
}


def _norm_importance(raw) -> str:
    """Map a provider's importance label to our canonical vocabulary."""
    if raw is None:
        return "low"
    key = str(raw).strip().lower()
    if not key:
        return "low"
    return _IMPORTANCE_MAP.get(key, key if key in {"high", "medium", "low", "holiday"} else "low")


# --------------------------------------------------------------------------- #
# Cache helpers
# --------------------------------------------------------------------------- #

def _cache_path(day: datetime) -> pathlib.Path:
    return CACHE_DIR / f"economic_calendar_{day.strftime('%Y-%m-%d')}.json"


def _read_cache(day: datetime, max_age_hours: float = CACHE_MAX_AGE_HOURS):
    """Return cached events for `day` if fresh enough, else None."""
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
        return payload.get("events", [])
    except Exception:
        return None


def _write_cache(events: list, day: datetime) -> None:
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        path = _cache_path(day)
        with path.open("w") as fh:
            json.dump(
                {
                    "fetched_at": datetime.now(timezone.utc).isoformat(),
                    "query_date": day.strftime("%Y-%m-%d"),
                    "count": len(events),
                    "events": events,
                },
                fh,
                indent=2,
            )
    except Exception as exc:  # pragma: no cover - cache must never be fatal
        print(f"[economic_calendar] cache write failed: {exc}", file=sys.stderr)


# --------------------------------------------------------------------------- #
# Provider 1 — Finnhub (needs API key)
# --------------------------------------------------------------------------- #

def _fetch_finnhub(start: datetime, end: datetime) -> list[dict] | None:
    """
    Fetch from Finnhub free-tier economic calendar.
    Returns list of normalised event dicts, or None if unavailable (no key /
    blocked / error).  Errors are logged to stderr but never raised.
    """
    key = os.environ.get("FINNHUB_API_KEY", "").strip()
    if not key:
        print("[economic_calendar] Finnhub: no FINNHUB_API_KEY in env — skipping "
              "(free tier requires a key).", file=sys.stderr)
        return None
    url = "https://finnhub.io/api/v1/calendar/economic"
    params = {
        "from": start.strftime("%Y-%m-%d"),
        "to": end.strftime("%Y-%m-%d"),
        "token": key,
    }
    try:
        resp = requests.get(url, params=params, headers=HTTP_HEADERS,
                            timeout=REQUEST_TIMEOUT)
        if resp.status_code == 401:
            print("[economic_calendar] Finnhub: API key rejected (401).",
                  file=sys.stderr)
            return None
        resp.raise_for_status()
        raw = resp.json().get("economicCalendar", []) or resp.json().get("data", [])
    except Exception as exc:
        print(f"[economic_calendar] Finnhub fetch failed: {exc}", file=sys.stderr)
        return None

    events = []
    for item in raw:
        try:
            ev_ts = item.get("time") or item.get("releaseTime") or ""
            dt_iso = ""
            t_short = ""
            d_short = ""
            if ev_ts:
                dt_iso = ev_ts
                d_short = ev_ts[:10]
                t_short = ev_ts[11:16] if len(ev_ts) > 16 else ""
            events.append({
                "date": d_short,
                "time": t_short,
                "datetime": dt_iso,
                "country": item.get("country", item.get("countryCode", "")),
                "event": item.get("event", item.get("name", "")),
                "importance": _norm_importance(item.get("impact")),
                "actual": item.get("actual", ""),
                "previous": item.get("prev", item.get("previous", "")),
                "consensus": item.get("estamate", item.get("forecast",
                               item.get("consensus", item.get("estimate", "")))),
                "source": "finnhub",
            })
        except Exception:
            continue
    return events


# --------------------------------------------------------------------------- #
# Provider 2 — Trading Economics (needs client + key)
# --------------------------------------------------------------------------- #

def _fetch_tradingeconomics(start: datetime, end: datetime) -> list[dict] | None:
    client = os.environ.get("TRADINGECONOMICS_CLIENT", "").strip()
    key = os.environ.get("TRADINGECONOMICS_KEY", "").strip()
    if not client or not key:
        print("[economic_calendar] Trading Economics: missing "
              "TRADINGECONOMICS_CLIENT/_KEY — skipping.", file=sys.stderr)
        return None
    url = "https://api.tradingeconomics.com/calendar"
    params = {
        "c": client,
        "key": key,
        "country": "united states",
        "from": start.strftime("%Y-%m-%d"),
        "to": end.strftime("%Y-%m-%d"),
    }
    try:
        resp = requests.get(url, params=params, headers=HTTP_HEADERS,
                            timeout=REQUEST_TIMEOUT)
        if resp.status_code == 401:
            print("[economic_calendar] Trading Economics: auth rejected (401).",
                  file=sys.stderr)
            return None
        resp.raise_for_status()
        raw = resp.json() if resp.text.strip().startswith("[") else resp.json()
    except Exception as exc:
        print(f"[economic_calendar] Trading Economics fetch failed: {exc}",
              file=sys.stderr)
        return None

    events = []
    for item in raw:
        try:
            dt = item.get("Date", "")
            events.append({
                "date": dt[:10] if dt else "",
                "time": dt[11:16] if len(dt) > 16 else "",
                "datetime": dt,
                "country": item.get("Country", "")[:3].upper() if item.get("Country") else "",
                "event": item.get("Event", ""),
                "importance": _norm_importance(item.get("Importance")),
                "actual": str(item.get("Actual", "") or ""),
                "previous": str(item.get("Previous", "") or ""),
                "consensus": str(item.get("Forecast", "") or ""),
                "source": "tradingeconomics",
            })
        except Exception:
            continue
    return events


# --------------------------------------------------------------------------- #
# Provider 3 — Forex Factory public JSON feed (free, no key)
# --------------------------------------------------------------------------- #

FF_FEEDS = [
    "https://nfs.faireconomy.media/ff_calendar_thisweek.json",
    "https://nfs.faireconomy.media/ff_calendar_nextweek.json",
]


def _fetch_forexfactory_json(start: datetime, end: datetime) -> list[dict]:
    """
    Fetch the Forex Factory keyless JSON feeds (current week + next week when
    published) and normalise to our schema.  404 on nextweek is expected early
    in the week and is ignored.
    """
    merged: list[dict] = []
    for url in FF_FEEDS:
        try:
            resp = requests.get(url, headers=HTTP_HEADERS,
                               timeout=REQUEST_TIMEOUT)
            if resp.status_code == 404:
                continue  # nextweek not published yet
            resp.raise_for_status()
            merged.extend(resp.json())
        except Exception as exc:
            print(f"[economic_calendar] ForexFactory feed {url} failed: {exc}",
                  file=sys.stderr)
            continue

    events: list[dict] = []
    for item in merged:
        try:
            dt_iso = item.get("date", "")
            d_short = dt_iso[:10]
            t_short = dt_iso[11:16] if len(dt_iso) > 16 else ""
            events.append({
                "date": d_short,
                "time": t_short,
                "datetime": dt_iso,
                "country": item.get("country", ""),
                "event": item.get("title", ""),
                "importance": _norm_importance(item.get("impact")),
                "actual": item.get("actual", ""),       # present only after release
                "previous": item.get("previous", ""),
                "consensus": item.get("forecast", ""),   # FF "forecast" == consensus
                "source": "forexfactory",
            })
        except Exception:
            continue
    return events


# --------------------------------------------------------------------------- #
# Provider 4 — HTML scrape fallback (best-effort)
# --------------------------------------------------------------------------- #

def _scrape_html_fallback(start: datetime, end: datetime) -> list[dict]:
    """
    Last-ditch attempt to scrape an economic calendar from a public web page.
    These pages sit behind Cloudflare bot-protection and commonly return HTTP
    403 to non-browser clients, so this is expected to fail in most
    environments.  Returns [] on any failure.
    """
    targets = [
        "https://www.forexfactory.com/calendar",
        "https://www.investing.com/economic-calendar/",
    ]
    for url in targets:
        try:
            resp = requests.get(url, headers=HTTP_HEADERS,
                                timeout=REQUEST_TIMEOUT)
            if resp.status_code != 200 or not resp.text:
                print(f"[economic_calendar] scrape {url} -> HTTP "
                      f"{resp.status_code} (blocked).", file=sys.stderr)
                continue
            # If we ever get HTML, try a light BeautifulSoup parse.  We do not
            # hard-depend on bs4 being installed for the main path.
            try:
                from bs4 import BeautifulSoup  # type: ignore
            except Exception:
                print("[economic_calendar] scrape: bs4 not available to parse.",
                      file=sys.stderr)
                return []
            soup = BeautifulSoup(resp.text, "html.parser")
            # Forex Factory / Investing DOMs differ widely and change often;
            # do a tolerant row scan rather than a brittle selector.
            rows = soup.select("table tr") or soup.select("tr")
            events = []
            for tr in rows:
                cells = [c.get_text(" ", strip=True) for c in tr.find_all(["td", "th"])]
                if len(cells) < 4:
                    continue
                # Heuristic: a row that mentions a known event keyword.
                blob = " ".join(cells).lower()
                if not any(k in blob for k in ("cpi", "fomc", "nfp", "gdp", "ppi",
                                              "retail", "claims", "rate", "pmi")):
                    continue
                events.append({
                    "date": "", "time": "", "datetime": "",
                    "country": "", "event": " | ".join(cells)[:200],
                    "importance": "low", "actual": "", "previous": "",
                    "consensus": "", "source": "scrape",
                })
            if events:
                return events
        except Exception as exc:
            print(f"[economic_calendar] scrape {url} error: {exc}", file=sys.stderr)
            continue
    print("[economic_calendar] All HTML scrape sources unavailable/blocked.",
          file=sys.stderr)
    return []


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #

def _in_window(event: dict, start: datetime, end: datetime) -> bool:
    """Keep events whose date falls within [start, end] inclusive."""
    d = (event.get("date") or "").strip()
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
        key = (e.get("date"), e.get("time"), e.get("country"), e.get("event"))
        if key in seen:
            continue
        seen.add(key)
        out.append(e)
    return out


def _fetch_all(start: datetime, end: datetime) -> list[dict]:
    """Run the provider cascade and return the best available event list."""
    # 1. Finnhub (key-gated)
    for provider in (_fetch_finnhub, _fetch_tradingeconomics):
        ev = provider(start, end)
        if ev:
            return _dedup(ev)

    # 3. Forex Factory keyless JSON (primary working source)
    ev = _fetch_forexfactory_json(start, end)
    if ev:
        return _dedup(ev)

    # 4. HTML scrape fallback (usually blocked, but try)
    ev = _scrape_html_fallback(start, end)
    if ev:
        return _dedup(ev)

    print("[economic_calendar] WARNING: no provider returned data.", file=sys.stderr)
    return []


def get_economic_calendar(days_ahead: int = 7, force: bool = False) -> list[dict]:
    """
    Return upcoming economic events for the next `days_ahead` days.

    Results are cached per-query-date as dated JSON files in
    ~/.hermes/market_data/economic_calendar/ and refreshed at most every
    CACHE_MAX_AGE_HOURS (unless force=True).

    Args:
        days_ahead: number of days forward from today (default 7).
        force:      bypass cache and re-fetch.

    Returns:
        list of event dicts (see module docstring for schema).
    """
    if days_ahead < 1:
        days_ahead = 1

    now = datetime.now()
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=days_ahead)

    # Try cache (covers today's query date).
    if not force:
        cached = _read_cache(now, max_age_hours=CACHE_MAX_AGE_HOURS)
        if cached is not None:
            windowed = [e for e in cached if _in_window(e, start, end)]
            if windowed:
                print(f"[economic_calendar] using cache ({len(windowed)} events "
                      f"in window).", file=sys.stderr)
                return windowed

    events = _fetch_all(start, end)
    windowed = [e for e in events if _in_window(e, start, end)]

    # Sort chronologically then by importance (high first).
    imp_rank = {"high": 0, "medium": 1, "low": 2, "holiday": 3}
    windowed.sort(key=lambda e: (e.get("date", ""), e.get("time", ""),
                                 imp_rank.get(e.get("importance", "low"), 2)))

    # Cache the full fetched set (so future queries with larger windows can reuse).
    if events:
        _write_cache(events, now)

    # Coverage note: FF nextweek feed is often unavailable until late Fri/Sat.
    last = max((e.get("date", "") for e in windowed), default="")
    if last and last < end.strftime("%Y-%m-%d"):
        print(f"[economic_calendar] NOTE: forward coverage ends {last}; "
              f"requested window through {end.strftime('%Y-%m-%d')} — the "
              f"free ForexFactory next-week feed is published later in the week.",
              file=sys.stderr)

    return windowed


def get_next_high_impact_events(days_ahead: int = 7, force: bool = False) -> list[dict]:
    """
    Return only high-impact upcoming economic events for the next
    `days_ahead` days.  (FOMC, CPI, NFP, GDP, PPI, retail sales, jobless
    claims, rate decisions, etc.)
    """
    all_events = get_economic_calendar(days_ahead=days_ahead, force=force)
    return [e for e in all_events if e.get("importance") == "high"]


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def _print_events(events: list[dict], title: str) -> None:
    print(f"\n{title} — {len(events)} events")
    print("-" * 96)
    if not events:
        print("  (none)")
        return
    hdr = f"{'Date':<12}{'Time':<7}{'Ctry':<6}{'Imp':<8}{'Event':<42}{'Cons':<10}{'Prev':<10}"
    print(hdr)
    print("-" * 96)
    for e in events:
        print(f"{e.get('date',''):<12}{e.get('time',''):<7}"
              f"{e.get('country',''):<6}{e.get('importance',''):<8}"
              f"{e.get('event','')[:41]:<42}"
              f"{str(e.get('consensus',''))[:9]:<10}"
              f"{str(e.get('previous',''))[:9]:<10}")
    srcs = sorted({e.get("source", "?") for e in events})
    print(f"\nsource(s): {', '.join(srcs)}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Fetch upcoming economic calendar")
    ap.add_argument("--days", type=int, default=7,
                    help="Days ahead to look (default 7)")
    ap.add_argument("--high-impact", action="store_true",
                    help="Show only high-impact events")
    ap.add_argument("--force", action="store_true",
                    help="Force refresh cache")
    args = ap.parse_args()

    events = get_economic_calendar(days_ahead=args.days, force=args.force)
    if args.high_impact:
        events = get_next_high_impact_events(days_ahead=args.days, force=args.force)
        _print_events(events, f"High-impact economic events (next {args.days}d)")
    else:
        _print_events(events, f"Economic calendar (next {args.days}d)")

    hi = [e for e in events if e.get("importance") == "high"]
    if hi and not args.high_impact:
        print(f"\n  >> {len(hi)} high-impact event(s) in this window — "
              f"see get_next_high_impact_events().")
