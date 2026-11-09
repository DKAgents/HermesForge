#!/usr/bin/env python3
"""hl_fills_store.py — read API for the US-07 Hyperliquid fills store.

The research swarm reads the wallet-level fills (address + closed PnL) written by
`ingest_hl_fills.py` to ~/.hermes/market_data/hl_fills/. Exposes:

  * `read_fills(start, end, markets=None, scope=None)` -> pandas DataFrame
  * `coverage()` -> per-scope, per-day status (pulled vs reported, gaps, as-of)
  * `gaps()` -> days where pulled != reported, or days missing from a range

Raises `FileNotFoundError` with a clear message when nothing is ingested yet, so a
caller can distinguish "no data" from "empty result". All reads are read-only.

Usage (research swarm):
    from scripts.data.hl_fills_store import read_fills, coverage
    df = read_fills("2026-11-07", "2026-11-08", markets=["BTC-PERP"])
    print(df[["ts","address","coin","side","price","size","realized_pnl"]].head())
"""

from __future__ import annotations

import json
import pathlib

import pandas as pd

from ingest_hl_fills import (
    DATA_DIR,
    MANIFEST_PATH,
    _day_path,
    iter_days,
    load_manifest,
    scope_slug,
)

# Columns the store guarantees (order-stable). ``realized_pnl`` is closed PnL;
# ``side`` is the aggressor direction (buy/sell); ``is_taker`` is the maker/taker
# role; ``direction`` is HL's Open Long / Close Short / ... semantics.
SCHEMA = [
    "ts", "market", "coin", "dex", "market_class", "address", "side",
    "direction", "price", "size", "notional", "fee", "fee_token",
    "realized_pnl", "is_taker", "is_liquidation", "oid", "tid", "block", "hash",
    "_asof",
]


def coverage() -> dict:
    """Per (scope, day) summary from the manifest."""
    return load_manifest()


def gaps() -> list[dict]:
    """Days recorded with pulled != reported (or incomplete)."""
    out = []
    for k, v in load_manifest().items():
        if v.get("gap") or v.get("status") != "complete":
            out.append({"key": k, **v})
    return out


def _resolve_scope(markets: list[str] | None, scope: str | None) -> str:
    if scope is not None:
        return scope
    return scope_slug(markets)


def read_fills(start: str, end: str, markets: list[str] | None = None,
               scope: str | None = None,
               columns: list[str] | None = None) -> pd.DataFrame:
    """Read fills for [start, end] (inclusive YYYY-MM-DD) into one DataFrame.

    ``markets`` selects the per-market scope (default "all"); pass ``scope`` to
    override the slug directly. ``columns`` subsets the returned frame (default all).
    """
    sc = _resolve_scope(markets, scope)
    days = iter_days(start, end)
    frames = []
    missing = []
    for d in days:
        p = _day_path(sc, d)
        if not p.exists():
            missing.append(d)
            continue
        frames.append(pd.read_parquet(p))
    if not frames:
        raise FileNotFoundError(
            f"no fills ingested for scope={sc!r} over {start}..{end}; "
            f"run ingest_hl_fills.py first")
    df = pd.concat(frames, ignore_index=True)
    if columns:
        keep = [c for c in columns if c in df.columns]
        if keep:
            df = df[keep]
    return df


if __name__ == "__main__":
    cov = coverage()
    if not cov:
        print("No fills ingested yet.")
        raise SystemExit(0)
    n_complete = sum(1 for v in cov.values() if v.get("status") == "complete")
    n_gap = sum(1 for v in cov.values() if v.get("gap"))
    print(f"fills store: {len(cov)} (scope,day) records, {n_complete} complete, "
          f"{n_gap} gapped")
    for k, v in sorted(cov.items()):
        print(f"  {k}: {v.get('status')} rows={v.get('rows_pulled')} "
              f"reported={v.get('reported_count')} gap={v.get('gap')}")