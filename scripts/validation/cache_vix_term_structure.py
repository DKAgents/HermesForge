#!/usr/bin/env python3
"""
cache_vix_term_structure.py — Enrich the local market-data cache with full
historical VIX spot (^VIX) and VIX 3-month (^VIX3M) daily series.

The pre-existing VIXINDEX.parquet cache only covered ~2 years (2024-2026),
which is insufficient for multi-sub-period backtests. This helper fetches the
full history back to 2018-10-01 (matching the stock universe start) and writes:
  ~/.hermes/market_data/VIXINDEX.parquet      (VIX spot, refreshed/extended)
  ~/.hermes/market_data/VIX3M.parquet         (VIX 3-month, NEW)

Safe improvement: extending VIX history only ADDS bars; existing scanners that
read VIXINDEX.parquet get strictly more regime context, never less.

Usage:
    python3 cache_vix_term_structure.py
"""
import pathlib
import pandas as pd
import yfinance as yf

CACHE_DIR = pathlib.Path.home() / ".hermes" / "market_data"
START = "2018-10-01"


def _fetch(sym: str, out_name: str) -> None:
    df = yf.download(sym, start=START, auto_adjust=True, progress=False)
    if df is None or len(df) == 0:
        print(f"[{sym}] no data returned")
        return
    df = df.copy()
    # yfinance returns MultiIndex columns when downloading a single ticker in
    # newer versions; flatten to simple columns.
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df.columns = [c.lower() for c in df.columns]
    keep = [c for c in ["open", "high", "low", "close", "volume"] if c in df.columns]
    df = df[keep].sort_index()
    df = df[~df.index.duplicated(keep="last")]
    out = CACHE_DIR / out_name
    df.to_parquet(out)
    print(f"[{sym}] wrote {len(df)} rows {df.index.min().date()} -> {df.index.max().date()} -> {out}")


def main():
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    _fetch("^VIX", "VIXINDEX.parquet")
    _fetch("^VIX3M", "VIX3M.parquet")


if __name__ == "__main__":
    main()
