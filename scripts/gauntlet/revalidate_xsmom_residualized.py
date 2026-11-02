"""revalidate_xsmom_residualized.py — US-211 BTC-RESIDUALIZED xsmom (research).

Read-only research driver. Re-runs US-182 cross-sectional momentum with the BTC
beta STRIPPED BEFORE ranking (the US-211 construction): each coin's daily
returns are regressed on BTC daily returns (rolling 60d beta, estimated on data
through t-1 -> look-ahead free), a residual-return series is built, and the
top-quintile long leg is ranked on the RESIDUALIZED cumulative return instead
of the raw return.

Produces a REAL side-by-side RAW-vs-RESIDUALIZED verdict through the SAME
G3 / CPCV(G4) / DSR/PBO(G5) / regime+beta-cluster(G6) machinery the raw run
used (reports/backtester/xsmom_costaware_revalidation.md), so the beta-or-alpha
question is answered on identical footing.

The raw prior result (for reference, from that report): G3 pass +0.5911 R /
PF 1.351, but G4/G5 FAIL (CPCV 10th-pct PF 0.72, PBO 0.56, DSR 0.66) -> it was
BTC-beta, not alpha.

Writes ONE trial to data/gauntlet/trials.jsonl (fresh param_hash) for the
residualized shipping config, counted toward G5. No live state, no leverage
(MARGIN_CAP stays 1.0), cost counted once inside xsmom's own model.

Usage:
    python3 revalidate_xsmom_residualized.py [--no-write]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import statistics
import sys

import numpy as np
import pandas as pd

_THIS_DIR = pathlib.Path(__file__).resolve().parent          # scripts/gauntlet
if str(_THIS_DIR) not in sys.path:
    sys.path.insert(0, str(_THIS_DIR))

import xsmom as x                                          # noqa: E402
import cpcv_harness as cpcv                                 # noqa: E402
import trials_ledger as ledger                              # noqa: E402
from revalidate_xsmom import load_all_daily, build_panel, to_cpcv_trades  # noqa: E402

BETA_WINDOW = 60          # rolling 60d BTC-beta estimation window (look-ahead free)


def residualize_beta(panel: pd.DataFrame, btc: pd.Series,
                     window: int = BETA_WINDOW) -> pd.DataFrame:
    """Strip the BTC-beta from each coin's daily returns, build a residual
    PRICE index per coin.

    beta[t] is estimated on the trailing `window` returns ENDING at t-1 (via
    .shift(1)), so the residual return at t uses only prior data -> no
    look-ahead. r_res[t] = r[t] - beta[t] * r_btc[t]; the residual index is the
    cumprod of (1 + r_res), so xsmom's momentum (P[t-1]/P[t-30] - 1) becomes the
    residualized cumulative return by construction.
    """
    ret = panel.pct_change()
    btc_ret = btc.pct_change()
    cov = ret.rolling(window).cov(btc_ret)
    var = btc_ret.rolling(window).var().reindex(ret.index)
    # div along axis=0: align the time-indexed var Series to the DataFrame's
    # ROW index (a bare `cov / var` aligns to COLUMNS -> all-NaN).
    beta = cov.div(var, axis=0).shift(1)        # beta uses data through t-1
    resid_ret = ret - beta.multiply(btc_ret, axis=0)
    idx = (1.0 + resid_ret.fillna(0.0)).cumprod()
    # align to the panel index (border rows carry NaN -> drop the warm-up)
    idx = idx.reindex(panel.index)
    return idx


def run_config(panel, btc, kappa, band_frac, rebal=7, label=""):
    """Run simulate_xsmom + G3 + CPCV/DSR/PBO + partition for one config."""
    nav, eps, diag = x.simulate_xsmom(panel, btc, params={
        "kappa": kappa, "band_frac": band_frac, "rebalance_period": rebal})
    g3 = x.xsmom_g3_record(eps)
    rs = eps["net_r"].astype(float) if len(eps) else pd.Series(dtype=float)
    sharpe = x.net_sharpe(eps)
    pf = x._pf(rs.tolist()) if len(eps) else 0.0

    trades = to_cpcv_trades(eps)
    cpcv_res = cpcv.run_cpcv(trades, n_groups=12, k_test=2,
                             holding_horizon_bars=7, embargo_bars=7,
                             n_trials_from_ledger=ledger.count())
    split_pfs = [m["pf"] for m in cpcv_res["split_metrics"] if m["trade_count"] > 0]
    pfs = {
        "median": statistics.median(split_pfs) if split_pfs else 0.0,
        "p10": float(np.percentile(split_pfs, 10)) if split_pfs else 0.0,
        "min": min(split_pfs) if split_pfs else 0.0,
    }

    part = x.partition_regime(eps)
    betas = x.name_btc_betas(panel, btc)

    return {
        "label": label, "n": len(eps),
        "mean_net_r": round(float(rs.mean()), 4) if len(eps) else 0.0,
        "net_sharpe": round(sharpe, 3), "pf": round(pf, 4),
        "g3": g3, "cpcv": {"pbo": cpcv_res["pbo"], "dsr": cpcv_res["dsr"],
                           "agg_sharpe": cpcv_res["sharpe"], "split_pf": pfs},
        "partition": part, "betas": betas,
        "nav": nav, "eps": eps,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-write", action="store_true", help="do not write the trial")
    args = ap.parse_args()

    print("=== US-211 BTC-residualized xsmom — real-data backtest ===\n")

    daily = load_all_daily(None, use_cache=True)
    panel, btc, meta = build_panel(daily)
    print(f"panel: {panel.shape[0]} days x {panel.shape[1]} names "
          f"({panel.index.min().date()} -> {panel.index.max().date()})")

    resid_panel = residualize_beta(panel, btc, window=BETA_WINDOW)

    print("\n--- RAW vs RESIDUALIZED (shipping config kappa=0.5 band=0.25) ---")
    raw = run_config(panel, btc, 0.5, 0.25, label="RAW")
    res = run_config(resid_panel, btc, 0.5, 0.25, label="RESID")
    for r in (raw, res):
        c = r["cpcv"]
        print(f"  [{r['label']:6s}] n={r['n']:3d}  meanR={r['mean_net_r']:+0.4f} "
              f"PF={r['pf']:.3f}  Sharpe={r['net_sharpe']:.3f}")
        print(f"            G3: optR={r['g3']['optimistic_mean_r']:+.4f} "
              f"realR={r['g3']['realistic_mean_r']:+.4f} "
              f"pessPF={r['g3']['pessimistic_pf']:.3f} passed={r['g3']['passed']}")
        print(f"            G4/G5: splitPF med={c['split_pf']['median']:.3f} "
              f"p10={c['split_pf']['p10']:.3f} min={c['split_pf']['min']:.3f} "
              f"PBO={c['pbo']:.3f} DSR={c['dsr']:.3f} aggSharpe={c['agg_sharpe']:.3f}")

    print("\n--- regime partition (mean net R / PF) ---")
    for r in (raw, res):
        p = r["partition"]
        for k in ("overlay_up", "overlay_down", "bull", "bear", "neutral"):
            v = p[k]
            print(f"  [{r['label']:6s}] {k:12s} n={v['n']:3d} "
                  f"meanR={v['mean_r']:+.4f} PF={v['pf']}")

    print("\n--- per-name BTC beta (rolling 30d) — RAW vs RESIDUAL ---")
    raw_betas = raw["betas"]
    res_betas = res["betas"]
    for nm in sorted(raw_betas, key=lambda k: -raw_betas[k]):
        print(f"  {nm:10s} raw_beta={raw_betas[nm]:+.2f}  resid_beta={res_betas[nm]:+.3f}")
    print(f"  mean |raw beta| = {np.mean([abs(v) for v in raw_betas.values()]):.3f}   "
          f"mean |resid beta| = {np.mean([abs(v) for v in res_betas.values()]):.3f}")

    # ── Write the residualized trial ──────────────────────────────────────────
    res_rs = res["eps"]["net_r"].astype(float)
    param_hash = hashlib.sha256(json.dumps({
        "construction": "btc_residualized_xsmom",
        "beta_window": BETA_WINDOW, "lookback": x.MOMENTUM_LOOKBACK_DAYS,
        "skip": x.MOMENTUM_SKIP_DAYS, "top_frac": x.TOP_FRAC,
        "kappa": 0.5, "band_frac": 0.25, "rebalance_period": 7,
        "gross_cap": x.GROSS_EXPOSURE_CAP, "margin_cap": x.MARGIN_CAP_FRAC,
    }, sort_keys=True).encode()).hexdigest()
    universe_str = ",".join(sorted(panel.columns))
    universe_hash = hashlib.sha256(universe_str.encode()).hexdigest()

    result = {
        "avg_r": res["mean_net_r"],
        "max_r": round(float(res_rs.max()), 4) if len(res_rs) else 0.0,
        "min_r": round(float(res_rs.min()), 4) if len(res_rs) else 0.0,
        "pf": res["pf"],
        "sharpe": res["net_sharpe"],
        "trade_count": res["n"],
        "win_rate": round(float((res_rs > 0).mean()), 6) if len(res_rs) else 0.0,
        "r_outliers_skipped": 0,
        "g3_passed": res["g3"]["passed"],
        "g3_realistic_mean_r": res["g3"]["realistic_mean_r"],
        "g3_pessimistic_pf": res["g3"]["pessimistic_pf"],
        "cpcv_split_pf_median": res["cpcv"]["split_pf"]["median"],
        "cpcv_split_pf_p10": res["cpcv"]["split_pf"]["p10"],
        "cpcv_split_pf_min": res["cpcv"]["split_pf"]["min"],
        "pbo": res["cpcv"]["pbo"],
        "dsr": res["cpcv"]["dsr"],
        "mean_abs_resid_beta": round(float(np.mean([abs(v) for v in res_betas.values()])), 4),
        "mean_abs_raw_beta": round(float(np.mean([abs(v) for v in raw_betas.values()])), 4),
        "construction": "btc_residualized",
    }
    period_start = panel.index.min().strftime("%Y-%m-%d")
    period_end = panel.index.max().strftime("%Y-%m-%d")

    if not args.no_write:
        entry = ledger.increment_trial(
            hypothesis_id="HYP-14",
            param_hash=param_hash,
            universe_hash=universe_hash,
            period_start=period_start,
            period_end=period_end,
            result=result,
        )
        print(f"\nwrote trial HYP-14  param_hash={entry['param_hash'][:16]}...  "
              f"chain_hash={entry['chain_hash'][:16]}...")
    else:
        print(f"\n[--no-write] trial NOT written. param_hash={param_hash[:16]}...")

    print("\nDone.")
    return 0


if __name__ == "__main__":
    sys.exit(main())