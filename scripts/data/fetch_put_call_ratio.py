#!/usr/bin/env python3
"""
fetch_put_call_ratio.py — CBOE daily put/call ratio

CBOE publishes daily options market statistics including the total and
equity-only put/call ratios. This module fetches the latest values and
caches them for reuse by the HermesForge trading-research stack.

Source priority (tried in order):
  1. https://www.cboe.com/us/options/market_statistics/daily/
     (server-rendered Next.js page; the ratios are embedded in the
     React flight payload as `optionsData.ratios` and the report date
     as `selectedDate`).
  2. https://cdn.cboe.com/api/us/options/market_statistics/historical/daily/
     (JSON historical endpoint — currently 403/AccessDenied from outside,
     but kept as a fallback in case it opens up).
  3. yfinance proxy: download ^VIX and derive a VIX-implied put/call
     proxy. The CBOE VIX put/call ratio is not directly available via
     yfinance, so we synthesise a *behavioural* proxy: when VIX is
     elevated traders buy more puts for protection, so we map the VIX
     level to an approximate total put/call ratio. This is explicitly a
     proxy and is flagged as such in the cache.

Caches to ~/.hermes/market_data/put_call.json
Refreshes if cache > 1 day old (CBOE updates once per trading day).

Usage:
    python3 fetch_put_call_ratio.py              # fetch/update
    python3 fetch_put_call_ratio.py --force       # force refresh
    python3 fetch_put_call_ratio.py --summary     # print summary only
"""

import sys
import json
import pathlib
import argparse
import requests
from datetime import datetime, timezone

DAILY_URL = "https://www.cboe.com/us/options/market_statistics/daily/"
HISTORICAL_JSON_URL = (
    "https://cdn.cboe.com/api/us/options/market_statistics/historical/daily/"
)
CACHE_PATH = pathlib.Path.home() / ".hermes" / "market_data" / "put_call.json"
CACHE_MAX_AGE_HOURS = 20  # CBOE updates daily; refresh once a day

HTTP_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept": "text/html,application/json,application/xhtml+xml,*/*;q=0.8",
}


# --------------------------------------------------------------------------- #
# Regime classification
# --------------------------------------------------------------------------- #
def classify_regime(ratio: float) -> str:
    """
    Classify sentiment from the total put/call ratio.

    > 1.0  -> fearful  (more puts than calls traded; hedging/fear dominant)
    < 0.7  -> complacent (calls dominate; greed/speculation)
    else   -> neutral
    """
    if ratio is None:
        return "neutral"
    if ratio > 1.0:
        return "fearful"
    if ratio < 0.7:
        return "complacent"
    return "neutral"


# --------------------------------------------------------------------------- #
# Source 1: CBOE daily HTML page (Next.js flight payload)
# --------------------------------------------------------------------------- #
def _extract_flight_payloads(html: str):
    """Yield decoded JSON-ish strings from `self.__next_f.push([1,"..."])` calls."""
    import re

    for m in re.finditer(r'self\.__next_f\.push\(\[1,"(.*?)"\]\)</script>', html, re.S):
        raw = m.group(1)
        try:
            # The payload uses escaped quotes / unicode escapes.
            decoded = raw.encode("utf-8").decode("unicode_escape")
        except Exception:
            decoded = raw
        yield decoded


def _balanced_json_substr(s: str, start: int) -> str:
    """Return the balanced JSON substring beginning at index `start` ('[' or '{')."""
    depth = 0
    open_ch = s[start]
    close_ch = "]" if open_ch == "[" else "}"
    in_str = False
    esc = False
    for i in range(start, len(s)):
        ch = s[i]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == open_ch:
            depth += 1
        elif ch == close_ch:
            depth -= 1
            if depth == 0:
                return s[start : i + 1]
    raise ValueError("unbalanced JSON in flight payload")


def fetch_from_daily_html() -> dict:
    """
    Fetch the CBOE daily market-statistics page and extract put/call ratios
    from the embedded Next.js flight payload.

    Returns dict: {date, total_ratio, equity_ratio, source, ratios}
    Raises on failure.
    """
    resp = requests.get(DAILY_URL, headers=HTTP_HEADERS, timeout=30)
    resp.raise_for_status()
    html = resp.text

    import json

    selected_date = None
    ratios_raw = None

    for payload in _extract_flight_payloads(html):
        if selected_date is None and '"selectedDate"' in payload:
            import re

            m = re.search(r'"selectedDate":"([^"]+)"', payload)
            if m:
                selected_date = m.group(1)
        if ratios_raw is None and '"ratios"' in payload:
            j = payload.find('"ratios"')
            arr_start = payload.find("[", j)
            try:
                ratios_raw = json.loads(_balanced_json_substr(payload, arr_start))
            except Exception:
                ratios_raw = None

    if not ratios_raw:
        raise RuntimeError("could not locate put/call ratios in CBOE daily HTML")

    ratio_map = {r["name"]: r["value"] for r in ratios_raw}

    total_ratio = ratio_map.get("TOTAL PUT/CALL RATIO")
    equity_ratio = ratio_map.get("EQUITY PUT/CALL RATIO")

    total_ratio = float(total_ratio) if total_ratio is not None else None
    equity_ratio = float(equity_ratio) if equity_ratio is not None else None

    return {
        "date": selected_date or datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "total_ratio": total_ratio,
        "equity_ratio": equity_ratio,
        "source": "cboe_daily_html",
        "ratios": ratio_map,
    }


# --------------------------------------------------------------------------- #
# Source 2: CBOE historical JSON endpoint (fallback)
# --------------------------------------------------------------------------- #
def fetch_from_historical_json() -> dict:
    """
    Attempt the CBOE historical daily JSON endpoint.

    The endpoint shape (when accessible) is a JSON object with per-day ratio
    records. We robustly scan the JSON for TOTAL/EQUITY ratio keys.
    """
    resp = requests.get(HISTORICAL_JSON_URL, headers=HTTP_HEADERS, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    # Defensive: locate the most recent record with total & equity ratios.
    # We support several plausible shapes.
    records = None
    if isinstance(data, list):
        records = data
    elif isinstance(data, dict):
        for key in ("data", "results", "rows", "records"):
            if isinstance(data.get(key), list):
                records = data[key]
                break
    if not records:
        # Maybe a single latest-record object
        records = [data]

    def _find_float(obj, names):
        if not isinstance(obj, dict):
            return None
        for k, v in obj.items():
            kl = str(k).lower()
            for n in names:
                if n in kl:
                    try:
                        return float(v)
                    except (TypeError, ValueError):
                        return None
        return None

    for rec in reversed(records):
        total = _find_float(
            rec,
            ["total put/call", "total_p_c", "totalpcr", "total put call"],
        )
        equity = _find_float(
            rec,
            ["equity put/call", "equity_p_c", "equity pcr", "equity put call"],
        )
        date = None
        if isinstance(rec, dict):
            for k in ("date", "tradeDate", "trade_date", "asOf"):
                if k in rec:
                    date = rec[k]
                    break
        if total is not None:
            return {
                "date": date or datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                "total_ratio": total,
                "equity_ratio": equity,
                "source": "cboe_historical_json",
                "ratios": rec if isinstance(rec, dict) else {},
            }

    raise RuntimeError("no usable put/call record in historical JSON")


# --------------------------------------------------------------------------- #
# Source 3: yfinance VIX proxy (last-resort fallback)
# --------------------------------------------------------------------------- #
def fetch_from_yfinance_proxy() -> dict:
    """
    Download ^VIX via yfinance and derive a *behavioural* put/call proxy.

    Rationale: when VIX is elevated, hedging demand rises and the put/call
    ratio tends to climb. We map the VIX close to an approximate total
    put/call ratio using a monotonic mapping calibrated to long-run CBOE
    norms (~0.7 average, rising sharply above VIX 25):

        proxy = 0.55 + 0.015 * VIX        (capped to [0.4, 2.0])

    This is explicitly a proxy; `source` is flagged accordingly.
    """
    import yfinance as yf

    vix = yf.Ticker("^VIX")
    hist = vix.history(period="5d", auto_adjust=False)
    if hist.empty:
        raise RuntimeError("yfinance returned no VIX data")
    vix_close = float(hist["Close"].iloc[-1])
    trade_date = str(hist.index[-1].date())

    proxy = 0.55 + 0.015 * vix_close
    proxy = max(0.4, min(2.0, proxy))

    return {
        "date": trade_date,
        "total_ratio": round(proxy, 2),
        "equity_ratio": round(proxy, 2),  # no equity-specific split available
        "source": "yfinance_vix_proxy",
        "vix_close": vix_close,
        "ratios": {},
        "proxy": True,
    }


# --------------------------------------------------------------------------- #
# Orchestration + cache
# --------------------------------------------------------------------------- #
def fetch_put_call_ratio(force: bool = False) -> dict:
    """
    Fetch the latest put/call ratio, trying each source in priority order.
    Returns a dict with at least: date, total_ratio, equity_ratio, source,
    regime. Caches the result to CACHE_PATH as JSON.
    """
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)

    if not force and CACHE_PATH.exists():
        try:
            cached = json.loads(CACHE_PATH.read_text())
            mtime = datetime.fromtimestamp(CACHE_PATH.stat().st_mtime, tz=timezone.utc)
            age_h = (datetime.now(timezone.utc) - mtime).total_seconds() / 3600
            if age_h < CACHE_MAX_AGE_HOURS:
                cached.setdefault("regime", classify_regime(cached.get("total_ratio")))
                return cached
        except (json.JSONDecodeError, OSError):
            pass  # corrupt cache -> refetch

    errors = []
    result = None
    for name, fn in (
        ("cboe_daily_html", fetch_from_daily_html),
        ("cboe_historical_json", fetch_from_historical_json),
        ("yfinance_vix_proxy", fetch_from_yfinance_proxy),
    ):
        try:
            result = fn()
            print(f"Put/Call: fetched via {name}", file=sys.stderr)
            break
        except Exception as e:  # noqa: BLE001
            errors.append(f"{name}: {e}")
            print(f"Put/Call: {name} failed ({e})", file=sys.stderr)

    if result is None:
        raise RuntimeError(
            "All put/call ratio sources failed:\n" + "\n".join(errors)
        )

    result.setdefault(
        "fetched_at", datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    )
    result["regime"] = classify_regime(result.get("total_ratio"))
    result["errors"] = errors

    CACHE_PATH.write_text(json.dumps(result, indent=2, default=str))
    print(f"Put/Call: cached to {CACHE_PATH}", file=sys.stderr)
    return result


def get_put_call_summary(force: bool = False) -> dict:
    """
    Return a concise summary:
        {total_ratio, equity_ratio, regime}
    where regime is 'fearful' (>1.0), 'complacent' (<0.7), or 'neutral'.
    """
    data = fetch_put_call_ratio(force=force)
    return {
        "total_ratio": data.get("total_ratio"),
        "equity_ratio": data.get("equity_ratio"),
        "regime": data.get("regime", classify_regime(data.get("total_ratio"))),
    }


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Fetch CBOE daily put/call ratio")
    ap.add_argument("--force", action="store_true", help="Force refresh cache")
    ap.add_argument(
        "--summary", action="store_true", help="Print summary dict only"
    )
    args = ap.parse_args()

    if args.summary:
        print(json.dumps(get_put_call_summary(force=args.force), indent=2))
    else:
        data = fetch_put_call_ratio(force=args.force)
        print(f"\nCBOE Put/Call Ratio — {data.get('date')}  (source: {data['source']})")
        print(f"  Total put/call ratio : {data.get('total_ratio')}")
        print(f"  Equity put/call ratio: {data.get('equity_ratio')}")
        print(f"  Regime              : {data['regime']}")
        if data.get("proxy"):
            print(f"  [VIX proxy — vix_close={data.get('vix_close')}]")
        print(f"\nCached to {CACHE_PATH}")
