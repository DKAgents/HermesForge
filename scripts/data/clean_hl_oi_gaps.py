"""clean_hl_oi_gaps.py — forward-fill isolated nulls in the HF OI/mark archive.

The HF dataset (`~/.hermes/market_data/hl_oi_hf/`) carries isolated null hours
(and a few fully-missing days, e.g. BTC 2025-06-12 / 2026-02-12 / 2026-07-08) in
mark_price/oracle_price/open_interest. A single missing day resamples to a NaN
daily close and NaN-poisons downstream rolling windows (~200d of a 200d SMA).

Fix: PAST-only forward-fill (ffill) of the price/OI columns, bounded to
`LIMIT` hours so a real long gap is not imputed far beyond a defensible window.
Leading nulls (before a coin's first reading — a not-yet-listed coin) are left
null. Output is a cleaned copy under `hl_oi_hf_clean/` (the raw source is
preserved untouched).

Usage: python3 clean_hl_oi_gaps.py
"""
from __future__ import annotations

import pathlib
import sys

import pandas as pd

SRC = pathlib.Path.home() / ".hermes" / "market_data" / "hl_oi_hf"
DST = pathlib.Path.home() / ".hermes" / "market_data" / "hl_oi_hf_clean"
FILL_COLS = ["mark_price", "oracle_price", "open_interest", "open_interest_usd"]
LIMIT = 168  # 7 days of hourly bars


def main() -> int:
    files = sorted(SRC.glob("*.parquet"))
    if not files:
        print(f"no source files under {SRC}", file=sys.stderr)
        return 1

    full = pd.concat(pd.read_parquet(f) for f in files)
    full = full.sort_values(["coin", "timestamp"])

    before = int(full[FILL_COLS].isna().sum().sum())
    full[FILL_COLS] = full.groupby("coin")[FILL_COLS].ffill(limit=LIMIT)
    after = int(full[FILL_COLS].isna().sum().sum())

    DST.mkdir(parents=True, exist_ok=True)
    full["_ym"] = full["timestamp"].dt.strftime("%Y-%m")
    n_out = 0
    for ym, g in full.groupby("_ym"):
        g = g.drop(columns=["_ym"])
        g.to_parquet(DST / f"{ym}.parquet", index=False)
        n_out += 1

    print(f"nulls {before} -> {after} (filled {before - after})")
    print(f"wrote {n_out} cleaned files to {DST}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())