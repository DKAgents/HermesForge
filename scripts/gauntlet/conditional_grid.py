"""conditional_grid.py — reusable conditional-characterization harness.

Pre-registered, OBJECTIVE regime classifier + per-regime x per-asset matrix
emitter. This is the "conditional-edge grid" the user has made a standing
requirement: for a strategy that is net-null (or net-negative) in aggregate,
does conditioning on {market regime x asset} surface any economically-motivated
sub-edge that the aggregate null hid?

Read-only. Writes no live state. No look-ahead, no leverage (the grid only
re-aggregates already-net trade rows the caller supplies).

── 1. Regime classifier (pre-registered, FIXED) ──────────────────────────────

REGIME = BTC trend on Hyperliquid native-perp mark_price, DAILY close (the
~/.hermes/market_data/hl_oi_hf/ archive). Three buckets, disjoint and
exhaustive, decided in priority order:

    (1) range     if  |close/SMA200 - 1| <= BAND            (inside the band)
    (2) risk_off  if  close < SMA200                         (pct < -BAND)
    (3) risk_on   if  close > SMA200  AND  SMA200 rising     (pct > +BAND, confirmed)
    (4) range     otherwise                                  (above band but NOT
                                                              confirmed rising)

BAND = 0.03  (the "narrow band" is +/-3%, documented here).  SMA window = 200.

Note the deliberate asymmetry (mirrors the spec): risk_off needs only "close <
SMA" (no slope requirement — being below trend is already bearish), whereas
risk_on needs BOTH "close > SMA" AND "SMA rising" (an uptrend must be
confirmed). "SMA rising" = SMA200[t] > SMA200[t-1] (strict). A day that is
above the band but whose SMA is not rising resolves to "range" (unconfirmed).

NO LOOK-AHEAD: regime[d] uses only BTC closes through day d. Days before the
200-day SMA exists are tagged None ("insufficient history") and are excluded
from splits; the caller reports the coverage truncation. The CALLER is
responsible for tagging each trade with the regime known at that trade's
signal-formation close (see the drivers): xsmom's signal uses closes through
t-1, so it reads regime as of t-1; the OI spread's signal uses closes through
t-1... through t (next-open fill), so it reads regime as of t. The module only
looks up whatever date the caller hands it.

── 2. Matrix emitter ─────────────────────────────────────────────────────────

Input `rows`: list of dicts, each
    {strategy, trade_date, coin, net_r, gross_r, [level]}
where `level` defaults to "name". Supported levels:
    "portfolio" -> one ROW PER HOLDING PERIOD carrying the STRATEGY's own net
                   (the official P&L). Aggregated only by regime.
    "name"      -> one row per coin per holding period (per-asset attribution).

Output (per strategy):
    regime_portfolio   {regime: {n, net_total, gross_total, pf, win_rate}}
                       (the official per-regime net — question (a))
    regime_name        {regime: {n, net_total, pf, win_rate}}
                       (sum of per-name attribution per regime — cross-check)
    asset_marginal     {coin: {n, net_total, pf, win_rate}}       (question (b))
    cells              {regime: {coin: {n, net_total, gross_total, pf, win_rate}}}
                       (the full per-regime x per-asset matrix — question (c))
    regime_counts      {regime: n_holding_periods}  (sample size per regime)

PF (profit factor) = sum(positive net) / |sum(negative net)|  (inf/0 conventions
as in the house _pf). win_rate = count(net>0) / count(total).

Unit note: the grid is unit-agnostic — it sums whatever `net_r`/`gross_r` the
caller passes. xsmom supplies net in R units (1R = 1% capital); the OI spread
supplies net in bps. Each strategy's cells are internally consistent.
"""

from __future__ import annotations

import glob
import pathlib
from typing import Callable, List, Optional

import numpy as np
import pandas as pd

# ── pre-registered constants (FIXED) ─────────────────────────────────────────
SMA_WINDOW = 200
BAND = 0.03

OI_DIR = pathlib.Path.home() / ".hermes" / "market_data" / "hl_oi_hf"

# ── 1. BTC regime series ─────────────────────────────────────────────────────


def load_btc_daily() -> pd.Series:
    """BTC native-perp (dex=='') mark_price DAILY close from hl_oi_hf.

    Returns a date-indexed Series of the last mark_price of each UTC day
    (last hourly observation), 2023-05-20 -> present (archive coverage).
    """
    files = sorted(glob.glob(str(OI_DIR / "*.parquet")))
    if not files:
        raise SystemExit(f"no parquet under {OI_DIR}")
    cols = ["timestamp", "coin", "dex", "mark_price"]
    parts = [pd.read_parquet(f, columns=cols) for f in files]
    df = pd.concat(parts, ignore_index=True)
    btc = df[(df["coin"] == "BTC") & (df["dex"] == "")].copy()
    btc["date"] = btc["timestamp"].dt.normalize()
    daily = (btc.sort_values("timestamp")
             .groupby("date", sort=True)["mark_price"].last())
    daily = daily[~daily.index.duplicated(keep="last")]
    # Forward-fill isolated missing days (max observed gap = 1 day) so the
    # 200-day SMA is not poisoned into NaN for 200 days after a single hole.
    daily = daily.sort_index().ffill(limit=7)
    return daily


def compute_regime(btc_close: pd.Series,
                   window: int = SMA_WINDOW,
                   band: float = BAND) -> pd.Series:
    """Classify each day into {'risk_on','risk_off','range'} per the header.

    btc_close: date-indexed daily closes. Returns a same-indexed Series of
    str labels; days before the SMA exists are NaN (insufficient history).
    """
    c = btc_close.astype(float)
    sma = c.rolling(window, min_periods=window).mean()
    sma_prev = sma.shift(1)
    labels = pd.Series(np.nan, index=c.index, dtype=object)

    above_band = (c - sma) / sma > band
    below_band = (c - sma) / sma < -band
    in_band = ~above_band & ~below_band & sma.notna()
    rising = sma > sma_prev

    labels[in_band] = "range"
    labels[below_band] = "risk_off"
    labels[above_band & rising] = "risk_on"
    labels[above_band & ~rising] = "range"   # above band but unconfirmed -> range
    return labels


# ── 2. aggregation helpers ───────────────────────────────────────────────────


def profit_factor(nets: np.ndarray) -> float:
    """sum(positive) / |sum(negative)|; inf if no losses and there is a gain;
    0.0 if no gains."""
    pos = float(np.nansum(nets[nets > 0]))
    neg = float(np.nansum(nets[nets < 0]))      # <= 0
    if neg < 0:
        return pos / abs(neg)
    return float("inf") if pos > 0 else 0.0


def win_rate(nets: np.ndarray) -> float:
    if nets.size == 0:
        return 0.0
    return float((nets > 0).sum() / nets.size)


def _agg(nets: np.ndarray, gross: np.ndarray) -> dict:
    return {
        "n": int((~np.isnan(nets)).sum() if nets.size else 0),
        "net_total": float(np.nansum(nets)),
        "gross_total": float(np.nansum(gross)) if gross is not None else 0.0,
        "pf": profit_factor(nets),
        "win_rate": win_rate(nets),
    }


# ── 3. main entry point ──────────────────────────────────────────────────────


def build_grid(rows: List[dict], regime: pd.Series) -> dict:
    """Emit the per-regime x per-asset matrix (see header for schema)."""
    port_rows = [r for r in rows if r.get("level", "name") == "portfolio"]
    name_rows = [r for r in rows if r.get("level", "name") == "name"]

    out: dict = {}

    for strategy in sorted({r["strategy"] for r in rows}):
        sr = {}
        p = [r for r in port_rows if r["strategy"] == strategy]
        nm = [r for r in name_rows if r["strategy"] == strategy]

        # regime -> dated rows, splitting by regime lookup
        def _map(rs):
            d = {}
            for r in rs:
                reg = _lookup(regime, r["trade_date"])
                if reg is None:
                    continue
                d.setdefault(reg, []).append(r)
            return d

        pmap = _map(p)
        nmap = _map(nm)

        sr["regime_portfolio"] = {r: _agg(_nets(pmap[r]), _gross(pmap[r]))
                                  for r in sorted(pmap)}
        sr["regime_name"] = {r: _agg(_nets(nmap[r]), _gross(nmap[r]))
                             for r in sorted(nmap)}
        sr["regime_counts"] = {r: len(pmap[r]) if p else len(nmap[r])
                               for r in sorted(set(pmap) | set(nmap))}

        # per-asset + cells (name rows only)
        coins = {}
        for r in nm:
            coins.setdefault(r["coin"], []).append(r)
        sr["asset_marginal"] = {c: _agg(_nets(v), _gross(v))
                                for c, v in sorted(coins.items(),
                                                   key=lambda kv: -len(kv[1]))}

        cells = {}
        for r in nm:
            reg = _lookup(regime, r["trade_date"])
            if reg is None:
                continue
            cells.setdefault(reg, {}).setdefault(r["coin"], []).append(r)
        sr["cells"] = {reg: {c: _agg(_nets(v), _gross(v))
                             for c, v in sorted(cd.items(),
                                                key=lambda kv: -len(kv[1]))}
                       for reg, cd in sorted(cells.items())}

        out[strategy] = sr

    return out


def _nets(rs) -> np.ndarray:
    return np.asarray([float(r["net_r"]) for r in rs], dtype=float)


def _gross(rs) -> np.ndarray:
    if not rs or "gross_r" not in rs[0]:
        return np.asarray([], dtype=float)
    return np.asarray([float(r["gross_r"]) for r in rs], dtype=float)


def _lookup(regime: pd.Series, date) -> Optional[str]:
    """Regime label at `date` (date/datetime/Timestamp); None if absent.

    Normalizes the tz of the lookup key to the index's own tz (naive<->UTC),
    so rows formed from tz-naive ms timestamps (xsmom) and tz-aware dates (OI)
    both match the regime index."""
    try:
        d = pd.Timestamp(date)
        idx = regime.index
        if hasattr(idx, "tz"):
            if idx.tz is not None and d.tz is None:
                d = d.tz_localize("UTC")
            elif idx.tz is None and d.tz is not None:
                d = d.tz_localize(None)
        val = regime.get(d) if hasattr(regime, "get") else regime.loc[d]
    except (KeyError, TypeError):
        return None
    if val is None or (isinstance(val, (float, np.floating)) and np.isnan(val)):
        return None
    return str(val)
