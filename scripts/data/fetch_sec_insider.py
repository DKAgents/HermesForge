#!/usr/bin/env python3
"""
fetch_sec_insider.py — SEC Form 4 insider trading feed

Pulls recent Form 4 (insider ownership change) filings from the SEC EDGAR
full-text search API, downloads each filing's XML, and parses out the
non-derivative open-market transactions. Only BUY (acquired) transactions
on tickers in the HermesForge universe are kept — insider buying is the
signal; selling is noise.

APIs (all free, no key, shared 10 req/sec rate limit):
  - Full-text search: https://efts.sec.gov/LATEST/search-index?q=...
  - Filing XML:       https://www.sec.gov/Archives/edgar/data/<cik>/<adsh-no-dashes>/<file>
  - CIK->ticker map:  https://www.sec.gov/files/company_tickers.json
  - Submissions:      https://data.sec.gov/submissions/CIK<zero-padded-cik>.json

A User-Agent header is mandatory for all SEC endpoints; we use:
    'HermesForge research@huggingface.co'

Caches to ~/.hermes/market_data/insider/insider_buys.parquet
Refreshes if cache > 6 hours old.

Usage:
    python3 fetch_sec_insider.py              # fetch/update (last 7 days)
    python3 fetch_sec_insider.py --force       # force refresh
    python3 fetch_sec_insider.py --days 14     # widen search window
"""

import sys
import time
import json
import pathlib
import argparse
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone

import requests
import pandas as pd

# Make the sibling validation package importable when run as a script.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from validation.universe import get_universe  # noqa: E402

USER_AGENT = "HermesForge research@huggingface.co"
HEADERS = {"User-Agent": USER_AGENT}

SEARCH_URL = "https://efts.sec.gov/LATEST/search-index"
TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
ARCHIVES_BASE = "https://www.sec.gov/Archives/edgar/data/"

CACHE_DIR = pathlib.Path.home() / ".hermes" / "market_data" / "insider"
CACHE_PATH = CACHE_DIR / "insider_buys.parquet"
CACHE_MAX_AGE_HOURS = 6

# Politeness: SEC allows up to 10 req/sec. Keep us comfortably under.
REQUEST_DELAY = 0.13  # seconds between SEC requests (~7.7 req/s)

# Map reporting-owner relationship flags to a human role string.
def _role_from_xml(rel_el: ET.Element) -> str:
    is_dir = rel_el.findtext("isDirector") == "1"
    is_off = rel_el.findtext("isOfficer") == "1"
    is_ten = rel_el.findtext("isTenPercentOwner") == "1"
    is_other = rel_el.findtext("isOther") == "1"
    title = (rel_el.findtext("officerTitle") or "").strip()
    parts = []
    if is_dir:
        parts.append("Director")
    if is_off:
        parts.append("Officer" + (f" ({title})" if title else ""))
    if is_ten:
        parts.append("10% Owner")
    if is_other:
        parts.append("Other" + (f" ({title})" if title and not is_off else ""))
    return ", ".join(parts) if parts else "Unknown"


def _load_cik_ticker_map() -> dict:
    """Return {int_cik: ticker} from SEC company_tickers.json."""
    resp = requests.get(TICKERS_URL, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    raw = resp.json()
    mapping = {}
    for entry in raw.values():
        cik = entry["cik_str"]
        if isinstance(cik, str):
            cik = int(cik.lstrip("0") or "0")
        mapping[int(cik)] = entry["ticker"]
    return mapping


def _search_form4(startdt: str, enddt: str, max_hits: int = 2000) -> list:
    """
    Query EDGAR full-text search for Form 4 filings in the date window.
    Returns a list of hits (dicts) with at least: ciks, adsh, _id (doc filename).
    """
    hits = []
    size = 100
    frm = 0
    while frm < max_hits:
        params = {
            "q": '"Form 4"',
            "dateRange": "custom",
            "startdt": startdt,
            "enddt": enddt,
            "forms": "4",
            "from": str(frm),
            "size": str(size),
        }
        resp = requests.get(SEARCH_URL, params=params, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        batch = data.get("hits", {}).get("hits", [])
        if not batch:
            break
        hits.extend(batch)
        time.sleep(REQUEST_DELAY)
        total = data.get("hits", {}).get("total", {}).get("value", 0)
        frm += len(batch)
        if frm >= total or len(batch) < size:
            break
    return hits[:max_hits]


def _adsh_to_path(adsh: str) -> str:
    """0000067887-26-000028 -> 000006788726000028"""
    return adsh.replace("-", "")


def _parse_form4_xml(xml_bytes: bytes) -> list:
    """
    Parse one Form 4 XML document into a list of transaction dicts.
    Only non-derivative transactions are returned (the cash-equity buys
    that matter for the insider-buy signal).
    """
    rows = []
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError:
        return rows

    issuer_el = root.find("issuer")
    ticker = ""
    issuer_name = ""
    if issuer_el is not None:
        raw_sym = (issuer_el.findtext("issuerTradingSymbol") or "").strip()
        # Some issuers list multiple share classes (e.g. "MOGA/MOGB").
        ticker = raw_sym.split("/")[0].strip().upper()
        issuer_name = (issuer_el.findtext("issuerName") or "").strip()

    period = (root.findtext("periodOfReport") or "").strip()

    owner_el = root.find("reportingOwner")
    insider = ""
    role = ""
    if owner_el is not None:
        rid = owner_el.find("reportingOwnerId")
        if rid is not None:
            insider = (rid.findtext("rptOwnerName") or "").strip()
        rel = owner_el.find("reportingOwnerRelationship")
        if rel is not None:
            role = _role_from_xml(rel)

    # Non-derivative (common-stock) transactions.
    nd_table = root.find("nonDerivativeTable")
    if nd_table is not None:
        for tx in nd_table.findall("nonDerivativeTransaction"):
            tx_date = (tx.findtext("transactionDate/value") or period).strip()
            coding = tx.find("transactionCoding")
            tx_code = (coding.findtext("transactionCode") or "").strip() if coding is not None else ""
            shares_txt = tx.findtext("transactionAmounts/transactionShares/value")
            price_txt = tx.findtext("transactionAmounts/transactionPricePerShare/value")
            acq_disp = tx.findtext("transactionAmounts/transactionAcquiredDisposedCode/value")
            security = (tx.findtext("securityTitle/value") or "").strip()

            if acq_disp is None or shares_txt is None:
                continue
            # "A" => acquired (buy), "D" => disposed (sell)
            tx_type = "buy" if acq_disp.strip().upper() == "A" else (
                "sell" if acq_disp.strip().upper() == "D" else None
            )
            if tx_type is None:
                continue
            try:
                shares = float(shares_txt)
            except (TypeError, ValueError):
                shares = 0.0
            try:
                price = float(price_txt) if price_txt is not None else 0.0
            except (TypeError, ValueError):
                price = 0.0

            rows.append({
                "ticker": ticker,
                "issuer_name": issuer_name,
                "insider": insider,
                "role": role,
                "transaction_type": tx_type,      # buy / sell
                "transaction_code": tx_code,        # P, S, A, M, ...
                "security": security,
                "shares": shares,
                "price": price,
                "transaction_date": tx_date,
                "period_of_report": period,
            })
    return rows


def fetch_sec_insider(days: int = 7, max_filings: int = 2000) -> pd.DataFrame:
    """
    Fetch recent Form 4 insider transactions for the HermesForge universe.

    Steps:
      1. Load the SEC CIK->ticker map.
      2. Full-text search Form 4 filings in the last `days` days.
      3. Pre-filter hits whose issuer CIK maps to a universe ticker
         (avoids downloading filings we'll discard).
      4. Download + parse each matching filing's XML.
      5. Keep only BUY (acquired) non-derivative transactions.

    Returns a DataFrame with columns:
        ticker, issuer_name, insider, role, transaction_type, transaction_code,
        security, shares, price, transaction_date, period_of_report, filed_date, accession
    """
    universe = set(get_universe())
    end_dt = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    start_dt = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")

    print(f"[insider] searching Form 4 filings {start_dt}..{end_dt}", file=sys.stderr)
    hits = _search_form4(start_dt, end_dt, max_hits=max_filings)
    print(f"[insider] {len(hits)} Form 4 hits from EDGAR full-text search", file=sys.stderr)

    # CIK -> ticker map for cheap pre-filtering.
    try:
        cik_map = _load_cik_ticker_map()
        time.sleep(REQUEST_DELAY)
    except Exception as e:
        print(f"[insider] WARN could not load CIK map ({e}); will fetch all filings", file=sys.stderr)
        cik_map = {}

    # Build candidate list: (issuer_cik, adsh, doc_filename).
    candidates = []
    skipped_non_universe = 0
    skipped_unmapped = 0
    for hit in hits:
        src = hit.get("_source", {})
        ciks = src.get("ciks", [])
        adsh = src.get("adsh", "")
        doc_id = hit.get("_id", "")
        doc_file = doc_id.split(":", 1)[-1] if ":" in doc_id else ""
        if not adsh or not doc_file:
            continue
        # Issuer CIK is the LAST entry in ciks (reporting owners listed first).
        issuer_cik_raw = ciks[-1] if ciks else ""
        try:
            issuer_cik = int(issuer_cik_raw.lstrip("0") or "0")
        except (ValueError, AttributeError):
            issuer_cik = 0
        if cik_map:
            ticker = cik_map.get(issuer_cik)
            if ticker is None:
                # Some filings put issuer first; try the first cik too.
                try:
                    alt = int(ciks[0].lstrip("0") or "0") if ciks else 0
                    ticker = cik_map.get(alt)
                except (ValueError, AttributeError):
                    ticker = None
            if ticker is None:
                skipped_unmapped += 1
                continue
            if ticker not in universe:
                skipped_non_universe += 1
                continue
            candidates.append((issuer_cik, ticker, adsh, doc_file, src.get("file_date", "")))
        else:
            # No map: fetch everything (will be filtered post-parse by ticker).
            candidates.append((issuer_cik, "", adsh, doc_file, src.get("file_date", "")))

    print(f"[insider] {len(candidates)} candidates in universe "
          f"(skipped {skipped_non_universe} non-universe, {skipped_unmapped} unmapped)",
          file=sys.stderr)

    all_rows = []
    seen_accessions = set()
    for issuer_cik, hint_ticker, adsh, doc_file, filed_date in candidates:
        if adsh in seen_accessions:
            continue
        seen_accessions.add(adsh)
        url = f"{ARCHIVES_BASE}{issuer_cik}/{_adsh_to_path(adsh)}/{doc_file}"
        try:
            resp = requests.get(url, headers=HEADERS, timeout=30)
            if resp.status_code != 200:
                time.sleep(REQUEST_DELAY)
                continue
            rows = _parse_form4_xml(resp.content)
        except Exception as e:
            print(f"[insider] WARN parse failed for {adsh}: {e}", file=sys.stderr)
            rows = []
        for r in rows:
            r["filed_date"] = filed_date
            r["accession"] = adsh
        all_rows.extend(rows)
        time.sleep(REQUEST_DELAY)

    if not all_rows:
        return pd.DataFrame(columns=[
            "ticker", "issuer_name", "insider", "role", "transaction_type",
            "transaction_code", "security", "shares", "price",
            "transaction_date", "period_of_report", "filed_date", "accession",
        ])

    df = pd.DataFrame(all_rows)

    # If we had no CIK map, filter by the XML's own ticker now.
    if cik_map:
        df = df[df["ticker"].isin(universe)].copy()
    else:
        df = df[df["ticker"].isin(universe)].copy()

    # Keep only BUY transactions.
    df = df[df["transaction_type"] == "buy"].copy()

    # Parse dates.
    df["transaction_date"] = pd.to_datetime(df["transaction_date"], errors="coerce")
    df["filed_date"] = pd.to_datetime(df["filed_date"], errors="coerce")
    df = df.sort_values(["ticker", "transaction_date"]).reset_index(drop=True)
    return df


def load_sec_insider(force: bool = False, days: int = 7) -> pd.DataFrame:
    """Load insider buy data from cache or fetch fresh."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    if not force and CACHE_PATH.exists():
        mtime = datetime.fromtimestamp(CACHE_PATH.stat().st_mtime, tz=timezone.utc)
        age = (datetime.now(timezone.utc) - mtime).total_seconds() / 3600
        if age < CACHE_MAX_AGE_HOURS:
            return pd.read_parquet(CACHE_PATH)

    df = fetch_sec_insider(days=days)
    df.to_parquet(CACHE_PATH, index=False)
    print(f"[insider] {len(df)} buy rows cached to {CACHE_PATH}", file=sys.stderr)
    return df


def get_insider_summary(days: int = 30) -> dict:
    """
    Return a summary of recent insider BUYS in our universe.

    Returns:
        {
            ticker: {
                "insider": str, "role": str, "shares": float,
                "price": float, "date": str (YYYY-MM-DD),
                "transaction_code": str, "total_shares": float  # sum across that ticker
            },
            ...
        }
    Only the most recent buy per ticker is shown in the top-level fields,
    with total_shares aggregating all buys in the window for that ticker.
    """
    df = load_sec_insider()
    if df.empty:
        return {}
    # transaction_date is stored tz-naive (datetime64[us]); compare tz-naive.
    cutoff = pd.Timestamp.now() - pd.Timedelta(days=days)
    recent = df[df["transaction_date"] >= cutoff]
    if recent.empty:
        return {}

    summary = {}
    for ticker, group in recent.groupby("ticker"):
        group = group.sort_values("transaction_date", ascending=False)
        latest = group.iloc[0]
        summary[ticker] = {
            "insider": str(latest["insider"]),
            "role": str(latest["role"]),
            "shares": float(latest["shares"]),
            "price": float(latest["price"]),
            "date": str(latest["transaction_date"].date())
            if pd.notna(latest["transaction_date"]) else "",
            "transaction_code": str(latest["transaction_code"]),
            "total_shares": float(group["shares"].sum()),
            "num_buys": int(len(group)),
        }
    return summary


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Fetch SEC Form 4 insider trading data")
    ap.add_argument("--force", action="store_true", help="Force refresh cache")
    ap.add_argument("--days", type=int, default=7, help="Search window in days (default 7)")
    ap.add_argument("--max-filings", type=int, default=2000,
                    help="Cap on search hits scanned (default 2000)")
    args = ap.parse_args()

    df = fetch_sec_insider(days=args.days, max_filings=args.max_filings)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    df.to_parquet(CACHE_PATH, index=False)
    print(f"[insider] {len(df)} buy rows cached to {CACHE_PATH}", file=sys.stderr)

    print(f"\nSEC Form 4 Insider Buys (universe) — {len(df)} transactions")
    if not df.empty:
        by_ticker = df.groupby("ticker").agg(
            buys=("shares", "count"),
            total_shares=("shares", "sum"),
            avg_price=("price", "mean"),
        ).reset_index()
        print(f"\nPer-ticker summary ({len(by_ticker)} tickers with buys):")
        print(by_ticker.to_string(index=False))

        print(f"\nMost recent buys (up to 20):")
        recent = df.sort_values("transaction_date", ascending=False).head(20)
        for _, row in recent.iterrows():
            d = row["transaction_date"].date() if pd.notna(row["transaction_date"]) else "?"
            print(f"  {d} {row['ticker']:6s} {row['insider'][:25]:25s} "
                  f"{row['role'][:22]:22s} {int(row['shares']):>8d} @ ${row['price']:.2f} "
                  f"[{row['transaction_code']}]")

        print(f"\n--- get_insider_summary() sample ---")
        summ = get_insider_summary(days=args.days)
        for tk, info in list(summ.items())[:10]:
            print(f"  {tk}: {info}")
    else:
        print("No insider buys in universe for the window.")
