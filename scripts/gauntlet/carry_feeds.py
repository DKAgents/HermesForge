"""carry_feeds.py — HermesForge US-186/US-188: funding-carry consumer wiring.

The read-surface that funding_carry crosses with its funding edge:

  * read_cross_venue_basis(coin) -> basis_store.read_basis(coin)   (US-188)
        the cross-venue funding-APR spread + HL-vs-OKX price basis — the "real
        carry metric" (funding_carry §3.5).
  * read_positioning(coin)       -> hl_assetctx_store.read_positioning(coin)
        (US-186) open-interest + dayNtlVlm participation + markPx series.
  * oi_delta_quadrant_series(...)  the OI-delta quadrant proxy (flag F-B: HL
        exposes NO per-side OI/long-short ratio), derived from CONSECUTIVE
        snapshots via gauntlet/oi_delta.classify_oi_delta.

Deliberately NOT merged into funding_carry.py: that module is a PURE strategy
(DataFrames in, no store I/O — its store reads live in the driver
revalidate_funding_carry.py). This module is the shared read-surface both the
driver and the future live pipeline import, keeping the store dependency
one-way and acyclic:

  carry_feeds.py -> basis_store + hl_assetctx_store + oi_delta (+ funding_carry)
"""

from __future__ import annotations

import pathlib
import sys

import numpy as np
import pandas as pd

_THIS_DIR = pathlib.Path(__file__).resolve().parent          # scripts/gauntlet
_DATA_DIR = _THIS_DIR.parent / "data"                        # scripts/data
for _d in (str(_THIS_DIR), str(_DATA_DIR)):
    if _d not in sys.path:
        sys.path.insert(0, _d)

import basis_store          # noqa: E402
import hl_assetctx_store    # noqa: E402
from oi_delta import classify_oi_delta, QUADRANT_NEUTRAL  # noqa: E402


def read_cross_venue_basis(coin: str, start_ts: int | None = None,
                           end_ts: int | None = None) -> pd.DataFrame:
    """DataFrame[ts, hl_funding_apr, okx_funding_apr, funding_spread_apr,
    hl_mark, okx_last, price_basis_bps] — the cross-venue "real carry metric"
    (US-188). APR in percent, price basis in bps."""
    return basis_store.read_basis(coin, start_ts, end_ts)


def read_positioning(coin: str, start_ts: int | None = None,
                     end_ts: int | None = None) -> pd.DataFrame:
    """DataFrame[time, mark_px, open_interest, oi_usd, funding, premium,
    day_ntl_vlm, day_base_vlm, prev_day_px] (US-186). Consecutive rows feed
    oi_delta_quadrant_series."""
    return hl_assetctx_store.read_positioning(coin, start_ts, end_ts)


def oi_delta_quadrant_series(mark_px, open_interest,
                             threshold: float = 0.001) -> pd.Series:
    """OI-delta quadrant per CONSECUTIVE snapshot pair (US-186 §1.2 proxy).

    mark_px / open_interest: equally-long iterables (the positioning series).
    price_change_pct = mark[i]/mark[i-1] - 1, oi_change_pct = oi[i]/oi[i-1] - 1,
    classified via oi_delta.classify_oi_delta. First snapshot is 'neutral' (no
    prior). Returns a Series with one label per input row (index 0 = neutral)."""
    mark = pd.to_numeric(pd.Series(mark_px), errors="coerce").to_numpy()
    oi = pd.to_numeric(pd.Series(open_interest), errors="coerce").to_numpy()
    n = len(mark)
    labels = [QUADRANT_NEUTRAL] * n
    for i in range(1, n):
        m0, m1 = mark[i - 1], mark[i]
        o0, o1 = oi[i - 1], oi[i]
        if not (np.isfinite(m0) and np.isfinite(m1) and m0 != 0
                and np.isfinite(o0) and np.isfinite(o1) and o0 != 0):
            continue
        labels[i] = classify_oi_delta(float(m1 / m0 - 1.0),
                                      float(o1 / o0 - 1.0), threshold)
    return pd.Series(labels)


def latest_positioning_context(coin: str) -> dict:
    """Latest OI/positioning + OI-delta quadrant + dayNtlVlm participation for a
    coin (the OI-conditioning inputs for a funding-carry entry)."""
    df = read_positioning(coin)
    if df is None or df.empty:
        return {"coin": coin, "available": False}
    quadrant = oi_delta_quadrant_series(df["mark_px"], df["open_interest"])
    last = df.iloc[-1]
    return {
        "coin": coin, "available": True,
        "oi_usd": float(last["oi_usd"]) if np.isfinite(last["oi_usd"]) else None,
        "day_ntl_vlm": (float(last["day_ntl_vlm"])
                        if np.isfinite(last["day_ntl_vlm"]) else None),
        "oi_delta_quadrant": str(quadrant.iloc[-1]),
        "oi_delta_n": int((quadrant != QUADRANT_NEUTRAL).sum()),
    }