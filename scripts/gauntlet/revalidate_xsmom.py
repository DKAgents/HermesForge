"""revalidate_xsmom.py — HermesForge US-182 cost-aware cross-sectional momentum.

Read-only research driver. Fetches DEEP Hyperliquid 1d bars (same-venue, via the
candleSnapshot endpoint — the bars_1d.db store is EMPTY, see the findings section
in the emitted report), builds the daily panel, and produces the REAL
side-by-side NAIVE-vs-COST-AWARE verdict through xsmom_g3_record + CPCV/DSR/PBO.

Imports (driver -> xsmom + cpcv_harness + correlation_state + fee_source, all read).

Usage:
    python3 revalidate_xsmom.py [--coins ...] [--no-fetch-cache]
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import sys
import time

import numpy as np
import pandas as pd

_THIS_DIR = pathlib.Path(__file__).resolve().parent          # scripts/gauntlet
if str(_THIS_DIR) not in sys.path:
    sys.path.insert(0, str(_THIS_DIR))
_SCRIPTS_DIR = _THIS_DIR.parent                                # scripts/
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

import requests  # noqa: E402

import xsmom as x                                          # noqa: E402
import cpcv_harness as cpcv                                 # noqa: E402
from hermes_config.universe import CRYPTO_UNIVERSE          # noqa: E402

HYPERLIQUID_INFO_URL = "https://api.hyperliquid.xyz/info"
DROP_NAMES = {"kBONK", "kPEPE", "kSHIB", "PAXG"}            # F7 kilocoin/PAXG exclusion
BACKTEST_UNIVERSE = [n for n in CRYPTO_UNIVERSE if n not in DROP_NAMES]

_CACHE = pathlib.Path.home() / ".hermes" / "cache" / "scratch" / "xsmom_1d_bars.json"


def fetch_hl_daily_bars(coin: str, lookback_days: int = 4 * 365) -> list[dict]:
    """One candleSnapshot call returns HL's entire retained 1d floor (~1461 bars
    for majors), ascending by 't'. Returns [{ts, open, high, low, close, volume,
    trades}] (the ingest_hl_bars.fetch_candles schema). Read-only HTTP."""
    now = int(time.time() * 1000)
    start = now - lookback_days * 86400000
    r = requests.post(HYPERLIQUID_INFO_URL,
                      json={"type": "candleSnapshot",
                            "req": {"coin": coin, "interval": "1d",
                                    "startTime": start, "endTime": now}},
                      timeout=30)
    r.raise_for_status()
    data = r.json()
    if not isinstance(data, list) or not data:
        return []
    bars = []
    for c in data:
        bars.append({"ts": int(c["t"]), "open": float(c["o"]), "high": float(c["h"]),
                     "low": float(c["l"]), "close": float(c["c"]),
                     "volume": float(c["v"]),
                     "trades": int(c["n"]) if c.get("n") is not None else None})
    return sorted(bars, key=lambda b: b["ts"])


def load_all_daily(universe: list[str], use_cache: bool = True) -> dict[str, pd.DataFrame]:
    """Fetch (or load from cache) HL 1d bars. Returns {coin: DataFrame[ts, close, volume]}."""
    if use_cache and _CACHE.exists():
        with open(_CACHE) as f:
            raw = json.load(f)
        out = {}
        for coin, rows in raw.items():
            out[coin] = pd.DataFrame(rows)
        return out

    out = {}
    for i, coin in enumerate(universe):
        bars = fetch_hl_daily_bars(coin)
        if bars:
            out[coin] = pd.DataFrame(bars)[["ts", "close", "volume"]]
        print(f"  fetch {coin:10s} {len(bars)} bars", file=sys.stderr)
        if i < len(universe) - 1:
            time.sleep(0.15)
    if use_cache:
        _CACHE.parent.mkdir(parents=True, exist_ok=True)
        with open(_CACHE, "w") as f:
            json.dump({c: df.to_dict("records") for c, df in out.items()}, f)
    return out


def build_panel(daily: dict[str, pd.DataFrame]) -> tuple[pd.DataFrame, pd.Series, dict]:
    """Pivot to close panel on daily timestamps; ffill <= 2-day gaps; drop names
    whose source history is too short. Returns (close_panel, btc_close, meta).

    All bars are 100% Hyperliquid (same-venue) -> F13 provenance floor is met by
    construction (no OKX proxy mixing)."""
    frames = {}
    for coin, df in daily.items():
        d = df.copy()
        d["day"] = pd.to_datetime(d["ts"], unit="ms").dt.normalize()
        # bar-close series keyed by UTC day
        s = d.set_index("day")["close"]
        s = s[~s.index.duplicated(keep="last")].sort_index()
        frames[coin] = s

    panel = pd.DataFrame(frames)
    # full daily calendar from the union min..max, forward-fill gaps <= 2 days
    start = panel.index.min()
    end = panel.index.max()
    full_idx = pd.date_range(start, end, freq="D")
    panel = panel.reindex(full_idx)
    panel = panel.ffill(limit=2)

    # liquidity + vol floor (F7), computed on the trailing 30-day window
    names = list(panel.columns)
    kept = []
    meta = {}
    for nm in names:
        c = panel[nm]
        v = daily[nm].set_index(pd.to_datetime(daily[nm]["ts"], unit="ms")
                                .dt.normalize())["volume"]
        v = v[~v.index.duplicated(keep="last")].sort_index()
        v = v.reindex(c.index).ffill(limit=2)
        notional = (v * c).rolling(30).median().iloc[-1]
        meta[nm] = {"notional_usd": float(notional) if np.isfinite(notional) else 0.0,
                    "n_bars": int((~c.isna()).sum())}
        if panel[nm].notna().sum() >= (x.BTC_DMA_WINDOW + x.MOMENTUM_LOOKBACK_DAYS + 5):
            kept.append(nm)

    panel = panel[kept]
    btc = panel["BTC"] if "BTC" in panel else panel.iloc[:, 0]
    return panel, btc, meta


def to_cpcv_trades(episodes: pd.DataFrame) -> list[dict]:
    """Map episodes to cpcv_harness trade dicts {entry_time, exit_time, pnl_bps}."""
    trades = []
    for _, e in episodes.iterrows():
        trades.append({
            "entry_time": int(e["reb_ts"]),
            "exit_time": int(e["reb_ts"]) + x.REBALANCE_PERIOD * 86400000,
            "pnl_bps": float(e["net_r"]) * 100.0,   # R -> bps (scale-free for sharpe)
        })
    return trades


def run_config(panel, btc, kappa, band_frac, rebal=7):
    nav, eps, diag = x.simulate_xsmom(panel, btc, params={
        "kappa": kappa, "band_frac": band_frac, "rebalance_period": rebal})
    g3 = x.xsmom_g3_record(eps)
    sharpe = x.net_sharpe(eps)
    rs = eps["net_r"].astype(float)
    pf = x._pf(rs.tolist()) if len(eps) else 0.0
    return {"kappa": kappa, "band_frac": band_frac, "n": len(eps),
            "avg_turnover": round(float(eps["turnover"].mean()), 4) if len(eps) else 0.0,
            "mean_net_r": round(float(rs.mean()), 4) if len(eps) else 0.0,
            "net_sharpe": round(sharpe, 3), "pf": round(pf, 4),
            "g3": g3, "eps": eps, "nav": nav}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--coins", nargs="*", default=None)
    ap.add_argument("--no-cache", action="store_true")
    args = ap.parse_args()

    universe = args.coins if args.coins else BACKTEST_UNIVERSE
    print("=== US-182 cost-aware cross-sectional momentum — real-data backtest ===\n")

    daily = load_all_daily(universe, use_cache=not args.no_cache)
    panel, btc, meta = build_panel(daily)
    print(f"panel: {panel.shape[0]} days x {panel.shape[1]} names  "
          f"({panel.index.min().date()} -> {panel.index.max().date()})")

    # (a) current-window momentum rank
    print("\n--- (a) current momentum rank (30d, skip 1d) ---")
    mom_now = {}
    vol_now = {}
    for nm in panel.columns:
        c = panel[nm].dropna()
        if len(c) > x.MOMENTUM_LOOKBACK_DAYS:
            mom_now[nm] = x.momentum_at(c)
            vol_now[nm] = x.realized_vol_daily(c).dropna().iloc[-1]
    mser = pd.Series(mom_now).dropna().sort_values(ascending=False)
    n_long = max(1, int(round(len(mser) * x.TOP_FRAC)))
    for i, (nm, m) in enumerate(mser.items()):
        tag = "  <-- LONG leg" if i < n_long else ""
        print(f"  {i+1:2d}. {nm:10s} mom={m:+.2%}  vol={vol_now.get(nm,0):.1%}{tag}")

    # (b) partial vs naive + sweep
    print("\n--- (b) partial-rebalance vs naive full-turnover ---")
    results = {}
    for kappa, band in [(0.5, 0.25), (1.0, 0.0)]:
        results[(kappa, band)] = run_config(panel, btc, kappa, band)
    partial = results[(0.5, 0.25)]
    naive = results[(1.0, 0.0)]
    print(f"  {'config':24s} {'n':>4s} {'turnover':>9s} {'meanR':>8s} {'Sharpe':>8s} {'PF':>7s}")
    for key in [(0.5, 0.25), (1.0, 0.0)]:
        r = results[key]
        print(f"  kappa={r['kappa']:<5} band={r['band_frac']:<5}        "
              f"{r['n']:>4d} {r['avg_turnover']:>9.4f} {r['mean_net_r']:>+8.4f} "
              f"{r['net_sharpe']:>8.3f} {r['pf']:>7.3f}")

    print("\n  (b) turnout sweep (kappa x band_frac) — Sharpe vs turnover curve:")
    print(f"  {'kappa':>6s} {'band_frac':>9s} {'avg_turnover':>13s} {'net_sharpe':>11s} {'mean_net_r':>11s}")
    for kappa in (0.25, 0.5, 0.75, 1.0):
        for band in (0.0, 0.25, 0.5):
            r = run_config(panel, btc, kappa, band)
            print(f"  {kappa:>6.2f} {band:>9.2f} {r['avg_turnover']:>13.4f} "
                  f"{r['net_sharpe']:>11.3f} {r['mean_net_r']:>+11.4f}")

    # (c) G3 verdict for the shipping config
    print("\n--- (c) G3 verdict (xsmom_g3_record, shipping config kappa=0.5 band=0.25) ---")
    g3 = partial["g3"]
    print(f"  n={g3['n']}  optimistic_mean_r={g3['optimistic_mean_r']}  "
          f"realistic_mean_r={g3['realistic_mean_r']}  pessimistic_pf={g3['pessimistic_pf']}")
    print(f"  edge_decay_ratio={g3['edge_decay_ratio']}  passed={g3['passed']}")
    for reason in g3["reasons"]:
        print(f"    REJECT: {reason}")

    # CPCV + DSR/PBO on the shipping config
    print("\n--- (d) CPCV (N=12, k=2) + DSR/PBO ---")
    trades = to_cpcv_trades(partial["eps"])
    cpcv_res = cpcv.run_cpcv(trades, n_groups=12, k_test=2,
                             holding_horizon_bars=7, embargo_bars=7)
    print(f"  n_splits={cpcv_res['n_splits']}  n_paths={cpcv_res['n_paths']}  "
          f"PBO={cpcv_res['pbo']}  DSR={cpcv_res['dsr']}  agg_sharpe={cpcv_res['sharpe']}")
    split_pfs = [m["pf"] for m in cpcv_res["split_metrics"] if m["trade_count"] > 0]
    if split_pfs:
        import statistics
        print(f"  split PF: median={statistics.median(split_pfs):.3f}  "
              f"min={min(split_pfs):.3f}  10th-pct={np.percentile(split_pfs,10):.3f}")

    # regime + beta partition
    print("\n--- (e) regime + beta-cluster partition (shipping config) ---")
    part = x.partition_regime(partial["eps"])
    for k in ("overlay_up", "overlay_down", "bull", "bear", "neutral"):
        v = part[k]
        print(f"  {k:12s} n={v['n']:4d}  mean_net_r={v['mean_r']:+.4f}  pf={v['pf']}")

    betas = x.name_btc_betas(panel, btc)
    # per-name net P&L contribution (sum of weight * return over the run)
    nav = partial["nav"]
    print("\n  BTC beta per name (rolling 30d):")
    for nm in sorted(betas, key=lambda k: -betas[k]):
        print(f"    {nm:10s} beta={betas[nm]:+.2f}")

    print("\nDone.")
    return 0


if __name__ == "__main__":
    sys.exit(main())