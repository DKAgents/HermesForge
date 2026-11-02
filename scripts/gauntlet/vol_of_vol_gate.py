"""vol_of_vol_gate.py — HermesForge US-181: vol-of-vol timing gate (STUB).

US-181 (vol / variance-risk-premium timing) is NOT YET BUILT. This module is the
STUB consumer surface it will call — it reads the US-187 vol stores
(iv_store.dvol_index / crypto_atm_iv) and exposes the vol-of-vol LEVEL that
would gate a vol-timing entry ("is realized vol itself low/high enough to
justify the position?").

vol_of_vol_level = realized (annualized) vol of the DVOL index close over the
trailing window. It is a LEVEL measurement, not a signal; US-181 will layer its
entry/threshold logic on top when it lands.

Import direction (one-way, acyclic):
  vol_of_vol_gate.py -> iv_store.py
"""

from __future__ import annotations

import pathlib
import sys

import numpy as np
import pandas as pd

_THIS_DIR = pathlib.Path(__file__).resolve().parent          # scripts/gauntlet
_DATA_DIR = _THIS_DIR.parent / "data"                        # scripts/data
if str(_DATA_DIR) not in sys.path:
    sys.path.insert(0, str(_DATA_DIR))

import iv_store  # noqa: E402

HOURS_PER_YEAR = 8760


def vol_of_vol_level(currency: str = "BTC", window_hours: int = 30 * 24,
                     annualize: bool = True) -> float | None:
    """Realized vol of the DVOL index close (vol-of-vol) over the trailing
    `window_hours` hourly candles. Returns None if < 2 usable samples. The base
    unit is DVOL return per hour; annualize multiplies by sqrt(8760)."""
    dvol = iv_store.read_dvol(currency)
    if dvol is None or dvol.empty or "close" not in dvol.columns:
        return None
    closes = pd.to_numeric(dvol["close"], errors="coerce")
    lr = np.log(closes / closes.shift(1))
    lr = lr[np.isfinite(lr)]
    if len(lr) < 2:
        return None
    lr = lr[-window_hours:]
    if len(lr) < 2:
        return None
    std = float(lr.std(ddof=1))
    return std * (HOURS_PER_YEAR ** 0.5) if annualize else std


def vol_of_vol_gate(currency: str = "BTC",
                    threshold_ann: float = 0.5) -> dict:
    """STUB gate (US-181 pending): 'gated' = vol-of-vol above `threshold_ann`.
    The threshold is a PLACEHOLDER — US-181 must derive it from data, NOT adopt
    this default unvalidated (mirrors the empirically-justified-default rule)."""
    lvl = vol_of_vol_level(currency)
    if lvl is None:
        return {"currency": currency, "vol_of_vol_ann": None,
                "threshold_ann": threshold_ann, "gated": None,
                "reason": "no dvol history yet"}
    return {"currency": currency, "vol_of_vol_ann": lvl,
            "threshold_ann": threshold_ann, "gated": lvl > threshold_ann,
            "reason": None}