"""g4g5_hyp25_robustness.py — HYP-25 G4/G5 robustness pass (CPCV + DSR + PBO).

Backtester role. Runs the G4 CPCV and G5 DSR/PBO overfitting gates on HYP-25's
LIQUID-floor short leg (the HYP-25 spec: short the bottom-decile 7d-momentum
losers, restricted to names above the $250k trailing-OI floor).

Honesty rules baked in (per the run request):
  * INTEGER DAY NUMBERS for entry_time/exit_time — the cpcv_harness purge/embargo
    arithmetic is in the same integer unit as the timestamps; feeding ms/epoch
    or datetime mixes units and silently nullifies purge/embargo. We feed int
    day indices, and holding_horizon/embargo are in DAYS (max hold = 20d, so
    purge=20d, embargo=40d — the same 20/40 split the prior stock transfer audit
    used, restated in the daily-bar unit of this strategy).
  * NON-OVERLAPPING SAMPLES — the raw driver emits ~13.4k "trades" that are
    heavily serially-overlapping (a coin stuck in the bottom decile is re-shorted
    day after day while the prior short is still open). Overlapping returns
    under-state per-trade std and inflate Sharpe. We thin per-coin to
    non-overlapping holding windows (greedy chronological keep) and run CPCV on
    the thinned sample; the raw overlapping run is reported only as transparency.
  * DSR uses n_observations = distinct non-overlapping trades (NOT the harness's
    11x-stacked 66-fold concatenation) and n_trials = N read from the ledger.
  * Report is anchored on the honest +0.07R 2026 forward prior, and explicitly
    flags whether the OOS folds concentrate the pre-2026 positive vs the 2026
    decay.

Read-only on live state; LIVE off; no leverage beyond -1x; cost charged once
(4.5 bps/leg taker + 2.5 bps entry slip + hourly funding) exactly as the
HYP-25 driver nets it into net_r. No look-ahead (all signal/OI/funding at t).
"""
from __future__ import annotations

import hashlib
import json
import math
import pathlib
import sys

import numpy as np
import pandas as pd

_THIS_DIR = pathlib.Path(__file__).resolve().parent          # scripts/gauntlet
for _p in (_THIS_DIR, str(_THIS_DIR.parent)):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import trials_ledger as ledger                                              # noqa: E402
import cpcv_harness as cv                                                   # noqa: E402
from revalidate_hyp25_short_continuation import (                          # noqa: E402
    OI_FLOOR_USD, OI_TRAILING_WINDOW, TIMESTOP_BARS,
    indicators, load_daily_funding, load_daily_ohlc, load_daily_oi_usd,
    load_hourly_marks, run_short_trades, trailing_oi_matrix,
)

# ── G4/G5 harness parameters (fixed) ─────────────────────────────────────────
N_GROUPS = 12
K_TEST = 2
HOLDING_DAYS = 20      # purge window = max holding period (TIMESTOP_BARS days)
EMBARGO_DAYS = 40      # embargo = 2x holding, matching the prior transfer audit
N_TRIALS = ledger.count()   # N for DSR, read from the trials ledger


def _thin_non_overlapping(records):
    """Greedy per-coin thinning to non-overlapping holding windows.

    records are the raw HYP-25 liquid-leg trade dicts. Each carries trade_date
    (dates[t]) and bars_held (= exit_day - t); entry is at the START of day t+1.
    day_idx mapping: entry_idx = t+1, exit_idx = t + bars_held. Two same-coin
    trades overlap iff entry_idx <= last_kept_exit_idx. Cross-sectional breadth
    (different coins the same day) is preserved — that IS the strategy's edge.
    """
    # sort chronologically, stable by coin
    recs = sorted(records, key=lambda r: (r["trade_date"], r["coin"]))
    last_exit = {}
    kept = []
    for r in recs:
        t = r["_t"]
        entry_idx = t + 1
        exit_idx = t + r["bars_held"]
        c = r["coin"]
        if c in last_exit and entry_idx <= last_exit[c]:
            continue                     # overlaps a kept same-coin trade
        last_exit[c] = exit_idx
        kept.append(r)
    return kept


def _year_of(ts: pd.Timestamp) -> int:
    return ts.year


def main() -> int:
    print("=== HYP-25 G4/G5 robustness pass (LIQUID-floor short leg) ===\n")

    print("loading daily OHLC + funding + OI (real) ...")
    opens, highs, lows, closes = load_daily_ohlc()
    fundsum = load_daily_funding()
    oi_usd = load_daily_oi_usd()
    common = [c for c in closes.columns if c in fundsum.columns and c in oi_usd.columns]
    closes = closes[common]; opens = opens[common]
    highs = highs[common]; lows = lows[common]
    fundsum = fundsum[common]; oi_usd = oi_usd[common]
    print(f"  {len(common)} coins, {closes.shape[0]} days "
          f"({closes.index.min().date()} -> {closes.index.max().date()})")

    coins, O, H, L, C, ATR, M = indicators(opens, highs, lows, closes)
    F = fundsum.to_numpy(dtype=float).T
    OI = oi_usd.to_numpy(dtype=float).T
    dates = [pd.Timestamp(d) for d in closes.index]

    print("computing trailing OI floor matrix ...")
    OIt = trailing_oi_matrix(OI, OI_TRAILING_WINDOW)

    print("loading hourly marks (real) ...")
    Mh, hr_days = load_hourly_marks(common)
    uniq_days, first_idx = np.unique(np.asarray(hr_days, dtype=object),
                                     return_index=True)
    day_to_first = {uniq_days[i]: int(first_idx[i]) for i in range(len(uniq_days))}
    date_to_didx = {d: i for i, d in enumerate(dates)}
    hour_to_day = np.array([date_to_didx.get(d, -1) for d in hr_days],
                           dtype=np.int64)
    print(f"  hourly marks: {Mh.shape[0]} coins x {Mh.shape[1]} hours\n")

    print(f"-- LIQUID bottom-decile short leg (OI >= ${OI_FLOOR_USD:,.0f}) --")
    liq_records = run_short_trades(Mh, C, F, ATR, M, OIt, dates, coins,
                                   day_to_first, hour_to_day,
                                   floor_usd=OI_FLOOR_USD)
    # attach day index `_t` for entry/exit integer mapping
    tmap = {d: i for i, d in enumerate(dates)}
    for r in liq_records:
        r["_t"] = tmap[r["trade_date"]]
    print(f"  raw (overlapping) trades: {len(liq_records)}")

    nonov = _thin_non_overlapping(liq_records)
    print(f"  non-overlapping trades after per-coin thinning: {len(nonov)}")

    def to_cpcv(records):
        out = []
        for r in records:
            t = r["_t"]
            # entry at start of day t+1, exit at day t + bars_held (int day idx)
            out.append({
                "entry_time": int(t + 1),
                "exit_time": int(t + r["bars_held"]),
                "pnl_bps": float(r["net_r"]),   # R units (scale-free for PF/Sharpe)
                "coin": r["coin"],
                "trade_date": r["trade_date"],
                "net_r": float(r["net_r"]),
            })
        return out

    def run(records, label):
        tlist = to_cpcv(records)
        res = cv.run_cpcv(tlist, n_groups=N_GROUPS, k_test=K_TEST,
                          n_trials_from_ledger=N_TRIALS,
                          holding_horizon_bars=HOLDING_DAYS,
                          embargo_bars=EMBARGO_DAYS)
        pfs = sorted(m["pf"] for m in res["split_metrics"])
        n = len(pfs)
        p10 = pfs[int(math.ceil(0.10 * n)) - 1] if n else 0.0
        p50 = pfs[n // 2] if n else 0.0
        pmin = pfs[0] if n else 0.0
        print(f"\n  [{label}] CPCV N={N_GROUPS} k={K_TEST} splits={res['n_splits']} "
              f"paths={res['n_paths']} trades={len(tlist)}")
        print(f"    split PF: 10th-pct={p10:.4f}  median={p50:.4f}  min={pmin:.4f}")
        print(f"    harness PBO={res['pbo']:.4f}  (rank-based over {n} fold Sharpes)")
        return tlist, pfs, res

    tlist_ov, pfs_ov, res_ov = run(liq_records, "OVERLAPPING (transparency only)")
    tlist, pfs, res = run(nonov, "NON-OVERLAPPING (honest)")

    # ── DSR on the honest non-overlapping sample ────────────────────────────
    net = np.array([x["net_r"] for x in nonov])
    n_obs = len(net)
    avg = float(net.mean())
    std = float(net.std(ddof=1)) if n_obs > 1 else 1e-15
    sharpe = avg / std if std > 1e-15 else 0.0
    # population skew / excess kurtosis (Bailey & LdP use higher moments)
    skew = float(pd.Series(net).skew()) if n_obs > 2 else 0.0
    kurt = float(pd.Series(net).kurt()) if n_obs > 3 else 0.0
    dsr = cv.compute_dsr(sharpe, skew, kurt, N_TRIALS, n_obs)
    print(f"\n  [G5 DSR] non-overlapping sample: n={n_obs} mean={avg:+.4f}R "
          f"std={std:.4f}R sharpe={sharpe:.4f} skew={skew:.4f} kurt={kurt:.4f}")
    print(f"    N(trials ledger)={N_TRIALS}  DSR={dsr:.6f}")

    # ── Year decomposition (honest forward prior = 2026) ────────────────────
    print("\n  year decomposition of NON-OVERLAPPING liquid short leg (mean net R):")
    df = pd.DataFrame([
        {"year": _year_of(r["trade_date"]), "net_r": r["net_r"]}
        for r in nonov
    ])
    yr = df.groupby("year")["net_r"].agg(["count", "mean"])
    for y, row in yr.iterrows():
        print(f"    {y}: n={int(row['count']):5d}  mean={row['mean']:+.4f}R")
    print(f"    ALL: n={len(nonov)}  mean={df['net_r'].mean():+.4f}R")
    print(f"    2026 forward prior (honest): "
          f"{yr.loc[2026, 'mean']:+.4f}R" if 2026 in yr.index else "    (no 2026 trades)")

    # ── OOS fold concentration: does the edge live pre-2026? ────────────────
    # Reconstruct the 66 splits, label each OOS (test) trade by year, tally the
    # edge's contribution by year across all OOS folds.
    splits = cv.generate_cpcv_splits(tlist, N_GROUPS, K_TEST,
                                     HOLDING_DAYS, EMBARGO_DAYS)
    oos_year_net = {}
    oos_year_n = {}
    for s in splits:
        for t in s["test_trades"]:
            y = _year_of(t["trade_date"])
            oos_year_net[y] = oos_year_net.get(y, 0.0) + t["net_r"]
            oos_year_n[y] = oos_year_n.get(y, 0) + 1
    print("\n  OOS fold concentration by year (across all 66 splits' test trades):")
    for y in sorted(oos_year_net):
        print(f"    {y}: n={oos_year_n[y]:6d}  sum_net_R={oos_year_net[y]:+9.1f}  "
              f"mean={oos_year_net[y]/oos_year_n[y]:+.4f}R")

    # ── parameter hash for the robustness harness (fresh) ───────────────────
    param_dict = {
        "construction": "hyp25_g4g5_robustness",
        "hypothesis_id": "HYP-25",
        "leg": "liquid_floor_short",
        "oi_floor_usd": OI_FLOOR_USD,
        "cpcv_n_groups": N_GROUPS,
        "cpcv_k_test": K_TEST,
        "holding_days": HOLDING_DAYS,
        "embargo_days": EMBARGO_DAYS,
        "non_overlapping": True,
        "dsr_n_trials": N_TRIALS,
        "dsr_n_observations": n_obs,
        "live": "off",
        "leverage": "none_-1x_max",
    }
    param_hash = hashlib.sha256(
        json.dumps(param_dict, sort_keys=True).encode()).hexdigest()
    print(f"\n  fresh param_hash (robustness harness): {param_hash[:16]}...")

    # collect deliverable JSON for the report
    out = {
        "param_hash": param_hash,
        "n_trials_ledger": N_TRIALS,
        "raw_trades": len(liq_records),
        "non_overlapping_trades": len(nonov),
        "cpcv": {
            "n_splits": res["n_splits"],
            "n_paths": res["n_paths"],
            "pf_10th_pct": pfs[int(math.ceil(0.10 * len(pfs))) - 1],
            "pf_median": pfs[len(pfs) // 2],
            "pf_min": pfs[0],
            "pbo": res["pbo"],
        },
        "dsr": {
            "n_observations": n_obs,
            "sharpe": sharpe,
            "skew": skew,
            "kurtosis": kurt,
            "dsr": dsr,
        },
        "year_mean_net_r": {int(y): float(v) for y, v in yr["mean"].items()},
        "year_counts": {int(y): int(v) for y, v in yr["count"].items()},
        "oos_concentration": {
            str(y): {"n": oos_year_n[y], "sum_net_r": float(oos_year_net[y]),
                     "mean": float(oos_year_net[y] / oos_year_n[y])}
            for y in sorted(oos_year_net)
        },
    }
    outpath = pathlib.Path.home() / ".hermes" / "cache" / "scratch" / "hyp25_g4g5_result.json"
    with open(outpath, "w") as f:
        json.dump(out, f, indent=2, default=str)
    print(f"  result saved to {outpath}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
