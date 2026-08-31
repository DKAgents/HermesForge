#!/usr/bin/env python3
"""
fetch_short_interest.py — Short interest data feed for the HermesForge universe

Short interest measures how many shares of a stock have been sold short and
not yet repurchased. It is published twice per month (around the 15th and the
end of the month, on settlement). High short interest (as a % of float) and a
high short-interest ratio (days-to-cover) flag crowded shorts and potential
short-squeeze candidates.

Source priority (tried in order; each falls back gracefully on failure):
  1. FINRA Reg SHO short interest — published twice monthly. We attempt the
     modern FINRA data API (https://api.finra.org/data/groups/...). From a
     datacenter IP this endpoint frequently 404s / is region-restricted, so it
     is best-effort.
  2. Nasdaq short interest — https://www.nasdaqtrader.com/Trader.aspx?id=ShortInterest
     The per-symbol lookup is served by an ASP.NET AJAX callback
     (Server.BL_ShortInterest.SearchShortInterests); the bulk comma-delimited
     file is paywalled. We attempt the AJAX callback per ticker, best-effort.
  3. yfinance fallback — yfinance exposes short-interest fields inside
     `Ticker.info`: shortPercentOfFloat, shortRatio (days-to-cover),
     sharesShort, sharesShortPriorMonth, dateShortInterest, floatShares.
     This is the most reliable path from restricted IPs and is the default
     working source.

Each ticker record returned contains:
    ticker, name, short_interest_shares, short_pct_of_float (%),
    days_to_cover, float_shares, prior_short_interest_shares,
    change_shares, change_pct, report_date, source

Caches results to ~/.hermes/market_data/short_interest/short_interest_YYYY-MM-DD.json
Refreshes if the most recent cached dated file is < CACHE_MAX_AGE_HOURS old.

Usage:
    python3 fetch_short_interest.py                 # fetch/update (universe)
    python3 fetch_short_interest.py --force          # force refresh
    python3 fetch_short_interest.py --tickers AAPL TSLA
    python3 fetch_short_interest.py --high 10.0      # only SI > 10% of float
"""

import sys
import json
import time
import pathlib
import argparse
from datetime import datetime, timezone

import requests

# Make the sibling validation package importable when run as a script.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from validation.universe import get_universe  # noqa: E402

# Optional yfinance (primary reliable fallback).
try:
    import yfinance as yf
except Exception:  # pragma: no cover
    yf = None

# --------------------------------------------------------------------------- #
# Config
# --------------------------------------------------------------------------- #
CACHE_DIR = pathlib.Path.home() / ".hermes" / "market_data" / "short_interest"
CACHE_MAX_AGE_HOURS = 12  # FINRA publishes 2x/month; refresh twice a day is plenty

HTTP_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept": "application/json,text/html,*/*;q=0.8",
}

FINRA_API_BASE = "https://api.finra.org/data/groups/us-equity/regulated"
# FINRA short-interest dataset names vary over time; try each.
FINRA_DATASETS = [
    "short-interest",
    "shortInterest",
    "short-interest-monthly",
    "regShoShortInterest",
]
NASDAQ_AJAX_URL = "https://www.nasdaqtrader.com/Trader.aspx/SearchShortInterests"

# yfinance per-ticker request spacing (be polite; we hit one info call each).
YF_DELAY = 0.15


def _to_float(v, default=None):
    try:
        if v is None:
            return default
        f = float(v)
        return f
    except (TypeError, ValueError):
        return default


def _ts_to_date(ts, default=None):
    """Convert a yfinance epoch-seconds timestamp to YYYY-MM-DD."""
    if ts is None:
        return default
    try:
        return datetime.fromtimestamp(int(ts), tz=timezone.utc).strftime("%Y-%m-%d")
    except (TypeError, ValueError, OSError):
        return default


# --------------------------------------------------------------------------- #
# Source 1: FINRA Reg SHO short interest API (best-effort)
# --------------------------------------------------------------------------- #
def fetch_from_finra(tickers, timeout=30):
    """
    Attempt the FINRA data API for short interest.

    Returns a dict {ticker: record} on success, or raises RuntimeError on
    failure (endpoint down / 404 / unexpected shape). This is best-effort: the
    public FINRA short-interest endpoint is frequently restricted from
    datacenter IPs.
    """
    payload = {
        "fields": [
            "ticker",
            "shortInterest",
            "daysToCover",
            "settlementDate",
            "totalShares",
        ],
        "limit": 10000,
    }
    headers = {**HTTP_HEADERS, "Content-Type": "application/json"}
    last_err = None
    for ds in FINRA_DATASETS:
        url = f"{FINRA_API_BASE}/{ds}"
        try:
            r = requests.post(url, headers=headers, data=json.dumps(payload), timeout=timeout)
            if r.status_code == 404:
                last_err = f"{ds} -> 404"
                continue
            r.raise_for_status()
            data = r.json()
            rows = _extract_rows(data)
            if rows is None:
                last_err = f"{ds} -> unparseable shape"
                continue
            return _finra_rows_to_records(rows, tickers)
        except Exception as e:
            last_err = f"{ds} -> {e!r}"
            continue
    raise RuntimeError(f"FINRA short-interest API unavailable: {last_err}")


def _extract_rows(data):
    """Locate the row list inside a FINRA API JSON response (defensive)."""
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("data", "rows", "results", "records", "items"):
            v = data.get(key)
            if isinstance(v, list):
                return v
    return None


def _finra_rows_to_records(rows, tickers):
    """Map FINRA rows to our normalized record shape keyed by ticker."""
    tset = set(tickers)
    out = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        tk = (row.get("ticker") or row.get("symbol") or row.get("Ticker") or "").upper()
        if not tk or (tset and tk not in tset):
            continue
        si = _to_float(row.get("shortInterest") or row.get("shortShares"))
        dtc = _to_float(row.get("daysToCover") or row.get("days_to_cover"))
        rep = row.get("settlementDate") or row.get("date")
        out[tk] = {
            "ticker": tk,
            "name": row.get("name") or row.get("companyName"),
            "short_interest_shares": si,
            "short_pct_of_float": _to_float(row.get("shortPercentOfFloat")),
            "days_to_cover": dtc,
            "float_shares": _to_float(row.get("floatShares") or row.get("float")),
            "prior_short_interest_shares": _to_float(row.get("priorShortInterest")),
            "change_shares": _to_float(row.get("change")),
            "change_pct": _to_float(row.get("changePercent") or row.get("changePct")),
            "report_date": rep,
            "source": "finra_api",
        }
    return out


# --------------------------------------------------------------------------- #
# Source 2: Nasdaq per-symbol AJAX (best-effort)
# --------------------------------------------------------------------------- #
def fetch_from_nasdaq(tickers, timeout=20):
    """
    Attempt the Nasdaq Trader per-symbol short-interest AJAX callback for each
    ticker. Returns {ticker: record}. Raises RuntimeError if every ticker
    fails (i.e. the endpoint is unreachable / blocked).

    Nasdaq exposes the lookup via an ASP.NET AJAX PageMethod named
    `SearchShortInterests`. We call it as a JSON POST.
    """
    headers = {**HTTP_HEADERS, "Content-Type": "application/json"}
    out = {}
    failures = 0
    for tk in tickers:
        try:
            r = requests.post(
                NASDAQ_AJAX_URL,
                headers=headers,
                data=json.dumps({"symbol": tk}),
                timeout=timeout,
            )
            if r.status_code != 200:
                failures += 1
                continue
            try:
                data = r.json()
            except ValueError:
                failures += 1
                continue
            rec = _parse_nasdaq_payload(data, tk)
            if rec is not None:
                out[tk] = rec
            else:
                failures += 1
        except Exception:
            failures += 1
            continue
        time.sleep(0.1)
    if not out:
        raise RuntimeError(
            f"Nasdaq short-interest AJAX returned no usable data "
            f"({failures}/{len(tickers)} tickers failed)"
        )
    return out


def _parse_nasdaq_payload(data, ticker):
    """
    The Nasdaq callback returns HTML fragments + a header string. We scrape
    numbers out of the rendered HTML for the standard columns:
    Short Interest, Days to Cover, Settlement Date.
    """
    import re

    text = ""
    if isinstance(data, dict):
        text = " ".join(str(v) for v in data.values())
    elif isinstance(data, str):
        text = data
    if not text:
        return None

    def grab(label, cast=float):
        # look for a number near a column label
        m = re.search(
            rf"{label}\s*</td>\s*<td[^>]*>\s*([0-9.,]+)", text, re.I
        )
        if m:
            try:
                return cast(m.group(1).replace(",", ""))
            except ValueError:
                return None
        return None

    si = grab("Short Interest")
    dtc = grab("Days To Cover|Days to Cover")
    rep = None
    m = re.search(r"Settlement Date\W+(\d{1,2}/\d{1,2}/\d{4})", text, re.I)
    if m:
        rep = m.group(1)
    if si is None:
        return None
    return {
        "ticker": ticker,
        "name": None,
        "short_interest_shares": _to_float(si),
        "short_pct_of_float": None,
        "days_to_cover": _to_float(dtc),
        "float_shares": None,
        "prior_short_interest_shares": None,
        "change_shares": None,
        "change_pct": None,
        "report_date": rep,
        "source": "nasdaq_ajax",
    }


# --------------------------------------------------------------------------- #
# Source 3: yfinance (reliable fallback)
# --------------------------------------------------------------------------- #
def fetch_from_yfinance(tickers, timeout=20):
    """
    Fetch short-interest fields from yfinance `Ticker.info` for each ticker.

    yfinance exposes:
      shortPercentOfFloat  (fraction, e.g. 0.0097 = 0.97%)
      shortRatio           (days to cover)
      sharesShort          (current short interest shares)
      sharesShortPriorMonth (previous report short interest shares)
      dateShortInterest    (epoch seconds, current report date)
      floatShares
    """
    if yf is None:
        raise RuntimeError("yfinance not installed; cannot use fallback source")

    out = {}
    for i, tk in enumerate(tickers):
        try:
            info = yf.Ticker(tk).info
        except Exception as e:
            print(f"[short_interest] yfinance error for {tk}: {e!r}", file=sys.stderr)
            continue

        if not info:
            continue

        si = _to_float(info.get("sharesShort"))
        si_prior = _to_float(info.get("sharesShortPriorMonth"))
        short_pct = _to_float(info.get("shortPercentOfFloat"))
        dtc = _to_float(info.get("shortRatio"))
        float_sh = _to_float(info.get("floatShares"))
        rep_date = _ts_to_date(info.get("dateShortInterest"))

        # shortPercentOfFloat is a fraction (0..1); convert to %.
        if short_pct is not None:
            short_pct_pct = short_pct * 100.0
        else:
            short_pct_pct = None

        change_sh = None
        change_pct = None
        if si is not None and si_prior is not None:
            change_sh = si - si_prior
            if si_prior != 0:
                change_pct = (change_sh / si_prior) * 100.0

        # If % of float missing but shares + float available, derive it.
        if short_pct_pct is None and si is not None and float_sh and float_sh > 0:
            short_pct_pct = (si / float_sh) * 100.0

        rec = {
            "ticker": tk,
            "name": info.get("shortName") or info.get("longName"),
            "short_interest_shares": si,
            "short_pct_of_float": short_pct_pct,
            "days_to_cover": dtc,
            "float_shares": float_sh,
            "prior_short_interest_shares": si_prior,
            "change_shares": change_sh,
            "change_pct": change_pct,
            "report_date": rep_date,
            "source": "yfinance",
        }
        out[tk] = rec

        if (i + 1) % 25 == 0:
            print(
                f"[short_interest] yfinance progress {i+1}/{len(tickers)}",
                file=sys.stderr,
            )
        time.sleep(YF_DELAY)

    if not out:
        raise RuntimeError("yfinance returned no usable short-interest data")
    return out


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def get_short_interest(tickers=None, force=False, use_cache=True):
    """
    Fetch short-interest data for `tickers` (defaults to the HermesForge
    universe). Uses yfinance (free, no key required). Returns a dict:

        {
            "as_of": "YYYY-MM-DD",
            "source": "yfinance" | "finra_api" | "nasdaq_ajax",
            "note": "...",
            "count": N,
            "stocks": [ {ticker, short_pct_of_float, days_to_cover, ...}, ... ]
        }

    Results are cached to a dated JSON file under CACHE_DIR.
    """
    if tickers is None:
        try:
            tickers = list(get_universe())
        except Exception:
            tickers = []
    tickers = [t.upper().strip() for t in tickers if t and t.strip()]
    # de-dup, preserve order
    tickers = list(dict.fromkeys(tickers))

    # Cache check: return latest dated file if fresh.
    if use_cache and not force:
        cached = _load_latest_cache()
        if cached is not None:
            return cached

    sources_tried = []

    # Source 1: FINRA — permanently disabled (endpoint returns 404 as of Aug 2026)
    # Nasdaq and yfinance provide equivalent data without the timeout.
    sources_tried.append("finra_api: skipped (endpoint offline)")

    # Source 2: Nasdaq — skipped (AJAX endpoint times out from VPS IPs as of Aug 2026)
    sources_tried.append("nasdaq_ajax: skipped (endpoint times out)")

    # Source 3: yfinance (primary — only working source as of Aug 2026)
    try:
        recs = fetch_from_yfinance(tickers)
        if recs:
            note = "yfinance fallback. " + "; ".join(sources_tried)
            result = _build_result(recs, tickers, "yfinance", note)
            _save_cache(result)
            return result
        sources_tried.append("yfinance: empty")
    except Exception as e:
        sources_tried.append(f"yfinance: {e!r}")
        print(f"[short_interest] yfinance failed: {e!r}", file=sys.stderr)

    # All sources failed.
    return {
        "as_of": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "source": "none",
        "note": "All short-interest sources failed: " + "; ".join(sources_tried),
        "count": 0,
        "stocks": [],
    }


def _build_result(recs_map, requested_tickers, source, note):
    """Assemble the normalized result payload from a {ticker: record} map."""
    stocks = []
    for tk in requested_tickers:
        rec = recs_map.get(tk)
        if rec is not None:
            stocks.append(rec)
    # Sort by short_pct_of_float descending (None last).
    stocks.sort(
        key=lambda r: (r.get("short_pct_of_float") is None, -(r.get("short_pct_of_float") or 0))
    )
    return {
        "as_of": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "source": source,
        "note": note,
        "count": len(stocks),
        "stocks": stocks,
    }


# --------------------------------------------------------------------------- #
# High short interest helper
# --------------------------------------------------------------------------- #
def get_high_short_interest_stocks(threshold=10.0, tickers=None, force=False):
    """
    Return the subset of stocks whose short interest (as % of float) exceeds
    `threshold` (default 10.0%). Falls back through the same source chain as
    get_short_interest().

    Returns a dict with the same shape as get_short_interest(); `stocks` only
    contains records with short_pct_of_float > threshold (None excluded).
    """
    data = get_short_interest(tickers=tickers, force=force)
    high = [
        s
        for s in data.get("stocks", [])
        if s.get("short_pct_of_float") is not None
        and s["short_pct_of_float"] > threshold
    ]
    high.sort(key=lambda r: -r["short_pct_of_float"])
    return {
        "as_of": data.get("as_of"),
        "source": data.get("source"),
        "note": data.get("note"),
        "threshold": threshold,
        "count": len(high),
        "stocks": high,
    }


# --------------------------------------------------------------------------- #
# Cache I/O
# --------------------------------------------------------------------------- #
def _cache_file_for_date(dt):
    return CACHE_DIR / f"short_interest_{dt}.json"


def _save_cache(result):
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    dt = result.get("as_of") or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    path = _cache_file_for_date(dt)
    with open(path, "w") as f:
        json.dump(result, f, indent=2)
    print(f"[short_interest] cached {result.get('count')} records -> {path}", file=sys.stderr)


def _load_latest_cache(max_age_hours=CACHE_MAX_AGE_HOURS):
    """Return the most recent fresh cached result, or None."""
    if not CACHE_DIR.exists():
        return None
    files = sorted(
        [p for p in CACHE_DIR.glob("short_interest_*.json")],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if not files:
        return None
    newest = files[0]
    mtime = datetime.fromtimestamp(newest.stat().st_mtime, tz=timezone.utc)
    age_h = (datetime.now(timezone.utc) - mtime).total_seconds() / 3600
    if age_h > max_age_hours:
        return None
    try:
        with open(newest) as f:
            return json.load(f)
    except Exception as e:
        print(f"[short_interest] cache read failed ({newest}): {e!r}", file=sys.stderr)
        return None


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def _print_results(data, limit=40):
    src = data.get("source")
    note = data.get("note", "")
    print(f"\nShort Interest — source: {src} — {data.get('count')} stocks")
    if note:
        print(f"  ({note})")
    print(f"  as_of: {data.get('as_of')}")
    print()
    hdr = (
        f"{'TICKER':8s} {'SI%float':>9s} {'DaysCov':>8s} "
        f"{'ShortSh(M)':>11s} {'Prior(M)':>10s} {'Chg(M)':>9s} {'Chg%':>7s}  Report"
    )
    print(hdr)
    print("-" * len(hdr))
    for s in data.get("stocks", [])[:limit]:
        si_pct = s.get("short_pct_of_float")
        si_pct_s = f"{si_pct:8.2f}%" if si_pct is not None else "      n/a"
        dtc = s.get("days_to_cover")
        dtc_s = f"{dtc:8.2f}" if dtc is not None else "     n/a"
        sh = s.get("short_interest_shares")
        sh_s = f"{sh/1e6:11.3f}" if sh is not None else "        n/a"
        prior = s.get("prior_short_interest_shares")
        prior_s = f"{prior/1e6:10.3f}" if prior is not None else "       n/a"
        chg = s.get("change_shares")
        chg_s = f"{chg/1e6:+9.3f}" if chg is not None else "      n/a"
        chgp = s.get("change_pct")
        chgp_s = f"{chgp:+6.1f}%" if chgp is not None else "   n/a"
        rep = s.get("report_date") or ""
        print(
            f"{s.get('ticker',''):8s} {si_pct_s} {dtc_s} {sh_s} "
            f"{prior_s} {chg_s} {chgp_s}  {rep}"
        )
    if data.get("count", 0) > limit:
        print(f"\n... ({data['count'] - limit} more not shown)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Fetch short interest data")
    ap.add_argument("--force", action="store_true", help="Force refresh cache")
    ap.add_argument("--tickers", nargs="+", help="Specific tickers (default: universe)")
    ap.add_argument("--high", type=float, default=None,
                    help="Only show stocks with short interest > HIGH %% of float")
    ap.add_argument("--limit", type=int, default=40, help="Max rows to print (default 40)")
    args = ap.parse_args()

    if args.high is not None:
        data = get_high_short_interest_stocks(
            threshold=args.high, tickers=args.tickers, force=args.force
        )
    else:
        data = get_short_interest(
            tickers=args.tickers, force=args.force
        )

    _print_results(data, limit=args.limit)
