"""
fetch_data.py — HermesForge Phase 1A (US-054)
Downloads and caches daily OHLCV data for the universe via yfinance.

- Pulls from Oct 1 2018 to present (allows 90-day warm-up before Apr 2019)
- Caches as parquet at ~/.hermes/market_data/<TICKER>.parquet
- Re-fetches if cache is >7 days old
- Flags tickers with >5% missing bars
- Prints universe size and date range on completion
"""

import os
import sys
import time
import datetime
import pathlib
import pandas as pd
import yfinance as yf

# Add parent dir to path so universe.py is importable
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from universe import get_universe

CACHE_DIR = pathlib.Path.home() / ".hermes" / "market_data"
START_DATE = "2018-10-01"
VALID_SIGNAL_START = "2019-04-01"   # after 90-day warm-up
CACHE_MAX_AGE_DAYS = 7

# Sub-period labels (per ADR-004)
SUBPERIODS = [
    ("period1_bull",    "2019-04-01", "2021-12-31"),
    ("period2_bear",    "2022-01-01", "2023-12-31"),
    ("period3_current", "2024-01-01", "2099-12-31"),
]


def label_subperiod(date: pd.Timestamp) -> str:
    d = date.date()
    for name, start, end in SUBPERIODS:
        if datetime.date.fromisoformat(start) <= d <= datetime.date.fromisoformat(end):
            return name
    return "pre_warmup"


def cache_path(ticker: str) -> pathlib.Path:
    return CACHE_DIR / f"{ticker}.parquet"


def needs_refresh(ticker: str) -> bool:
    p = cache_path(ticker)
    if not p.exists():
        return True
    age = datetime.datetime.now() - datetime.datetime.fromtimestamp(p.stat().st_mtime)
    return age.days >= CACHE_MAX_AGE_DAYS


def fetch_ticker(ticker: str) -> pd.DataFrame | None:
    """Download OHLCV for one ticker. Returns None on failure."""
    try:
        df = yf.download(ticker, start=START_DATE, auto_adjust=True, progress=False)
        if df is None or df.empty:
            return None
        df.index = pd.to_datetime(df.index)
        # Flatten MultiIndex columns if present
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df.columns = [c.lower() for c in df.columns]
        df["ticker"] = ticker
        df["subperiod"] = df.index.map(label_subperiod)
        return df
    except Exception as e:
        print(f"  ERROR fetching {ticker}: {e}")
        return None


def check_quality(ticker: str, df: pd.DataFrame | None) -> bool:
    """Returns True if data quality is acceptable."""
    if df is None or df.empty:
        return False
    # Count expected trading days (rough: 252/yr)
    years = (df.index[-1] - df.index[0]).days / 365.25
    expected = int(years * 252)
    actual = len(df)
    missing_pct = max(0, (expected - actual) / expected)
    if missing_pct > 0.05:
        print(f"  WARN {ticker}: {missing_pct:.1%} missing bars ({actual}/{expected}) — flagged")
        return False
    return True


def fetch_all(force: bool = False) -> dict[str, bool]:
    """Fetch all universe tickers. Returns {ticker: quality_ok}."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    tickers = get_universe()
    quality = {}
    good = bad = skipped = 0

    for i, ticker in enumerate(tickers, 1):
        if not force and not needs_refresh(ticker):
            skipped += 1
            quality[ticker] = True  # assume cached = good
            continue

        print(f"[{i:3d}/{len(tickers)}] Fetching {ticker}...")
        df = fetch_ticker(ticker)
        ok = check_quality(ticker, df)
        quality[ticker] = ok

        if df is not None and ok:
            df.to_parquet(cache_path(ticker))
            good += 1
        else:
            bad += 1

        time.sleep(0.15)  # polite rate limit

    print(f"\n✅ Fetch complete: {good} fetched, {skipped} cached, {bad} failed/flagged")
    return quality


def load_ticker(ticker: str) -> pd.DataFrame | None:
    """Load a ticker from cache. Returns None if not cached."""
    p = cache_path(ticker)
    if not p.exists():
        return None
    df = pd.read_parquet(p)
    # Return only post-warmup data for signal scanning
    return df[df.index >= VALID_SIGNAL_START].copy()  # type: ignore[return-value]


def load_all(valid_only: bool = True) -> dict[str, pd.DataFrame]:
    """Load all cached tickers. Optionally filter to valid signal period."""
    result = {}
    for ticker in get_universe():
        df = load_ticker(ticker)
        if df is not None and len(df) > 100:
            result[ticker] = df
    print(f"Loaded {len(result)} tickers from cache (valid signal period from {VALID_SIGNAL_START})")
    return result


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Fetch HermesForge universe data")
    parser.add_argument("--force", action="store_true", help="Force re-fetch even if cache is fresh")
    args = parser.parse_args()

    quality = fetch_all(force=args.force)
    good_tickers = [t for t, ok in quality.items() if ok]
    print(f"\nUniverse: {len(get_universe())} tickers defined")
    print(f"Quality OK: {len(good_tickers)} tickers")
    print(f"Valid signal period: {VALID_SIGNAL_START} onward")
    print(f"Sub-periods: {[sp[0] for sp in SUBPERIODS]}")
    print(f"Cache location: {CACHE_DIR}")
