#!/usr/bin/env python3
"""revalidate_hyp21_correct_cost.py — HYP-21 re-run at the CORRECT cost model + G4/G5.

Read-only research driver. The prior HYP-20/21 runs charged COST_HURDLE_BPS_LEG=45
(90 bps round-trip) as the *decision* hurdle. That was a PROMPT ERROR, not the
real fee. This re-run uses the actual cost model:

  * TAKER_FEE_BPS = 4.5 /leg            (execution_sim.py)
  * fee_source round-trip = 12 bps      (taker 4.5*2 + slip 2.5 + funding 0.5)
  * G3 fill model: maker fill_prob=0.35, adverse_selection_bps=1.5
      -> maker-blended per-leg = 0.35*(maker 1.5 + adv 1.5) + 0.65*taker 4.5
                               = 3.975 bps/side
      -> per-position round-trip = 2*3.975 + 2.5 + 0.5 = 10.95 bps

The cross-sectional spread is LONG top-decile + SHORT bottom-decile = 2 positions,
so "both legs" cost = 2 * per-position round-trip.  Cost tiers (both legs, bps):

  * G3 maker-blend   = 21.90 bps   (fill-realism; NOT decision — passive fill undemonstrated)
  * fee_source taker = 24.00 bps   (REALISTIC / DECISION  — matches US-228 liquid ~20-28)
  * conservative     = 32.00 bps   (mid-cap all-taker: taker 4.5*2 + slip 6 + funding 1 = 16/leg x2)

DECISION uses 24 bps.  Escalates to G4 (CPCV 10th-pct PF >= 1.0) + G5 (DSR >= 0.95,
PBO <= 0.30) on the NET series at the decision cost.

Robustness note: the prior driver's "5d hold" was DAILY-rebalanced overlapping 5d
forward returns (n~886). Overlapping labels are autocorrelated and inflate Sharpe /
DSR t-stats, so the G4/G5 escalation here uses a NON-OVERLAPPING 5-day rebalance
(stride 5, n~178) as the honest OOS sample; the 1d daily series is non-overlapping
by construction.

No look-ahead, no leverage beyond +-1x, LIVE off.  Writes ONE trials-ledger entry
per composite (C-positioning, C-all) with a FRESH param_hash (cost model is part of
the param dict, so the hash differs from every prior run).

Usage: python3 revalidate_hyp21_correct_cost.py [--no-write]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import sys

import numpy as np

_THIS_DIR = pathlib.Path(__file__).resolve().parent
if str(_THIS_DIR) not in sys.path:
    sys.path.insert(0, str(_THIS_DIR))

import trials_ledger as ledger                                    # noqa: E402
import cpcv_harness as cpcv                                        # noqa: E402
import revalidate_hyp21_multifactor_composite as base              # noqa: E402

# ── Correct cost model (single source: fee_source + g0_cost_screen defaults) ──
MAKER_FILL_PROB = 0.35          # ADR-009 §2 / g0_cost_screen
ADVERSE_SELECTION_BPS = 1.5     # ADR-009 §3 / g0_cost_screen
TAKER_BPS = 4.5                 # execution_sim.TAKER_FEE_BPS / fee_source
MAKER_BPS = 1.5                 # fee_source maker
SLIPPAGE_BPS = 2.5              # fee_source slippage
FUNDING_BPS = 0.5               # fee_source funding

# per-position (one leg) round-trip, bps
_per_leg_maker_blend = 2 * (MAKER_FILL_PROB * (MAKER_BPS + ADVERSE_SELECTION_BPS)
                            + (1 - MAKER_FILL_PROB) * TAKER_BPS) + SLIPPAGE_BPS + FUNDING_BPS
_per_leg_taker = 2 * TAKER_BPS + SLIPPAGE_BPS + FUNDING_BPS            # = 12 bps (fee_source)
_per_leg_conservative = 2 * TAKER_BPS + 6.0 + 1.0                      # mid-cap slip anchor

# both-legs (spread = 2 positions), bps
COST_MAKER_BLEND_BPS = 2 * _per_leg_maker_blend
COST_FEE_SOURCE_BPS = 2 * _per_leg_taker                              # = 24 bps  (DECISION)
COST_CONSERVATIVE_BPS = 2 * _per_leg_conservative                     # = 32 bps

DECISION_COST_BPS = COST_FEE_SOURCE_BPS

HOLD_PRIMARY = 1
HOLD_5D = 5
N_GROUPS = 12
K_TEST = 2


def net_series_from_records(res: dict, hold: int) -> tuple[list[float], list[int]]:
    """Non-overlapping net returns + day-index from a cross_sectional_spread result.

    hold=1 -> every record (daily rebalance is non-overlapping).
    hold>1 -> subsample to a single phase (stride = hold) so consecutive windows
              do not overlap. Overlapping forward returns are autocorrelated and
              inflate Sharpe/DSR; this is the honest OOS sample.
    """
    records = res["records"]
    stride = 1 if hold <= 1 else hold
    nets, idxs = [], []
    for i in range(0, len(records), stride):
        nets.append(records[i]["net"])
        idxs.append(i)
    return nets, idxs


def _moments(x: np.ndarray) -> tuple[float, float, float, float]:
    n = len(x)
    mu = float(x.mean())
    sd = float(x.std(ddof=1)) if n > 1 else 0.0
    sharpe = mu / sd if sd > 1e-15 else 0.0
    skew = 0.0
    kurt = 0.0
    if n > 2 and sd > 1e-15:
        skew = float(np.sum(((x - mu) / sd) ** 3) * n / ((n - 1) * (n - 2)))
    if n > 3 and sd > 1e-15:
        kurt = float(np.sum(((x - mu) / sd) ** 4) * n * (n + 1)
                     / ((n - 1) * (n - 2) * (n - 3))
                     - 3.0 * (n - 1) ** 2 / ((n - 2) * (n - 3)))
    return sharpe, skew, kurt, mu


def robustness(nets: list[float], hold: int, ledger_n: int) -> dict:
    """G4 (CPCV split-PF distribution) + G5 (DSR, PBO) on a NET return series.

    PBO + split PF come from the house cpcv_harness (chronological 12/2 split).
    DSR is computed HONESTLY on the non-overlapping full-sample net series
    (n_obs = actual rebalance count, NOT the duplicated pooled test-trade count)
    to avoid inflating the deflated t-stat.
    """
    pnl_bps = [n * 1e4 for n in nets]
    trades = [{"entry_time": int(i), "exit_time": int(i) + hold, "pnl_bps": float(p)}
              for i, p in enumerate(pnl_bps)]

    res = cpcv.run_cpcv(
        trades, n_groups=N_GROUPS, k_test=K_TEST,
        n_trials_from_ledger=ledger_n,
        holding_horizon_bars=hold, embargo_bars=hold,
    )

    split_pfs = [m["pf"] for m in res["split_metrics"] if m["trade_count"] > 0]
    pct10_pf = float(np.percentile(split_pfs, 10)) if split_pfs else float("nan")
    med_pf = float(np.median(split_pfs)) if split_pfs else float("nan")

    # Honest DSR on the non-overlapping full sample (no split-test duplication).
    arr = np.asarray(pnl_bps, dtype=float)
    sharpe, skew, kurt, _mu = _moments(arr)
    dsr = cpcv.compute_dsr(sharpe, skew, kurt, max(1, ledger_n), len(arr))

    return {
        "pbo": res["pbo"],
        "dsr_honest": dsr,
        "dsr_pooled": res["dsr"],
        "agg_sharpe_pooled": res["sharpe"],
        "sharpe_nonoverlap": round(sharpe, 6),
        "split_median_pf": round(med_pf, 4),
        "split_pct10_pf": round(pct10_pf, 4),
        "n_splits": res["n_splits"],
        "n_paths": res["n_paths"],
        "n_obs_nonoverlap": len(arr),
        "n_trials": ledger_n,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-write", action="store_true")
    args = ap.parse_args()

    print("=== HYP-21 re-run @ CORRECT cost model + G4/G5 robustness ===\n")
    print(f"cost tiers (both-legs round-trip, bps):")
    print(f"  G3 maker-blend (fill_prob={MAKER_FILL_PROB}, adv_sel={ADVERSE_SELECTION_BPS}) "
          f"= {COST_MAKER_BLEND_BPS:.2f}")
    print(f"  fee_source taker   (4.5*2 + 2.5 slip + 0.5 funding = 12/leg x2)    "
          f"= {COST_FEE_SOURCE_BPS:.2f}  <-- DECISION")
    print(f"  conservative       (taker + 6 slip + 1 funding = 16/leg x2)         "
          f"= {COST_CONSERVATIVE_BPS:.2f}")

    fmt = lambda bps: bps / 1e4  # bps -> fraction

    # funding degeneracy (factor 3 drop decision — unchanged from prior run)
    frac_modal, modal = base.funding_degeneracy()
    funding_usable = frac_modal <= 0.50
    print(f"\nfactor 3 (funding): {frac_modal*100:.1f}% cells at modal {modal:.8f}/hr "
          f"-> {'usable' if funding_usable else 'DROPPED (tie degeneracy)'}")

    print("\nloading native-perp hourly OI -> daily panels ...")
    opens, closes, ois = base.load_oi_daily()
    n_coins = opens.shape[1]
    print(f"  OI panel: {opens.shape[0]} days x {n_coins} coins "
          f"({opens.index.min().date()} -> {opens.index.max().date()})")

    oi_log = np.log(ois.replace(0.0, np.nan))
    close_log = np.log(closes.replace(0.0, np.nan))

    f_oi_change = oi_log - oi_log.shift(base.OI_CHANGE_LOOKBACK)
    oi_mean90 = ois.shift(1).rolling(base.OI_LEVEL_WINDOW,
                                     min_periods=base.OI_LEVEL_WINDOW).mean()
    oi_std90 = ois.shift(1).rolling(base.OI_LEVEL_WINDOW,
                                    min_periods=base.OI_LEVEL_WINDOW).std()
    f_oi_level_ts = (ois - oi_mean90) / oi_std90.replace(0.0, np.nan)
    f_price_mom = close_log - close_log.shift(base.PRICE_MOM_LOOKBACK)

    z_oi_change = base.xs_zscore(f_oi_change)
    z_oi_level = base.xs_zscore(f_oi_level_ts)
    z_price_mom = base.xs_zscore(f_price_mom)

    c_positioning = z_oi_change + z_oi_level
    c_all = c_positioning + z_price_mom

    composites = {"C-positioning": c_positioning, "C-all": c_all}
    factor_lists = {
        "C-positioning": ["oi_change_7d", "oi_level_90d"],
        "C-all": ["oi_change_7d", "oi_level_90d", "price_mom_7d"],
    }

    ledger_n = ledger.count()
    period_start = str(opens.index.min().date())
    period_end = str(opens.index.max().date())
    universe = sorted(opens.columns.tolist())
    universe_hash = hashlib.sha256(",".join(universe).encode()).hexdigest()

    print("\n===== composites at CORRECT cost (both-legs bps) =====")
    results_by_composite = {}
    for name, sig in composites.items():
        print(f"\n--- {name} ---")
        results_by_composite[name] = {}
        for hold in (HOLD_PRIMARY, HOLD_5D):
            r_mb = base.cross_sectional_spread(sig, opens, hold, fmt(COST_MAKER_BLEND_BPS),
                                               f"{name}-hold{hold}-makerblend")
            r_fs = base.cross_sectional_spread(sig, opens, hold, fmt(COST_FEE_SOURCE_BPS),
                                               f"{name}-hold{hold}-feesource")
            r_cons = base.cross_sectional_spread(sig, opens, hold, fmt(COST_CONSERVATIVE_BPS),
                                                 f"{name}-hold{hold}-conservative")
            print(f"  hold={hold}d: gross {r_fs['mean_gross_bps']:+.2f} bps/reb   "
                  f"net@maker {r_mb['mean_net_bps']:+.2f}   "
                  f"net@fee_src {r_fs['mean_net_bps']:+.2f}   "
                  f"net@conserv {r_cons['mean_net_bps']:+.2f}   "
                  f"n_rebal={r_fs['n_rebalances']}  recon={r_fs['reconciled']}")

            # G4/G5 on the DECISION (fee_source) net series, non-overlapping
            nets, _ = net_series_from_records(r_fs, hold)
            rob = robustness(nets, hold, ledger_n)
            print(f"         G4/G5 @ decision ({COST_FEE_SOURCE_BPS}bps): "
                  f"n_obs={rob['n_obs_nonoverlap']}  splitPF med={rob['split_median_pf']} "
                  f"P10={rob['split_pct10_pf']}  PBO={rob['pbo']}  "
                  f"DSR(nonovlp)={rob['dsr_honest']}  sharpe={rob['sharpe_nonoverlap']}")
            results_by_composite[name][hold] = {
                "gross_bps": round(r_fs["mean_gross_bps"], 4),
                "net_maker_blend_bps": round(r_mb["mean_net_bps"], 4),
                "net_fee_source_bps": round(r_fs["mean_net_bps"], 4),
                "net_conservative_bps": round(r_cons["mean_net_bps"], 4),
                "n_rebalances": r_fs["n_rebalances"],
                "reconciled": r_fs["reconciled"],
                "robustness": rob,
            }

    # ── write trials (one per composite, fresh param_hash) ──────────────────
    for name in composites:
        param_dict = {
            "construction": "multifactor_cross_sectional_composite",
            "cost_model": "corrected",
            "composite": name,
            "factors": factor_lists[name],
            "taker_bps_leg": TAKER_BPS,
            "maker_bps": MAKER_BPS,
            "fee_source_round_trip_bps": _per_leg_taker,
            "maker_fill_prob": MAKER_FILL_PROB,
            "adverse_selection_bps": ADVERSE_SELECTION_BPS,
            "cost_both_legs_maker_blend_bps": round(COST_MAKER_BLEND_BPS, 4),
            "cost_both_legs_fee_source_bps": round(COST_FEE_SOURCE_BPS, 4),
            "cost_both_legs_conservative_bps": round(COST_CONSERVATIVE_BPS, 4),
            "decision_cost_bps": DECISION_COST_BPS,
            "oi_change_lookback": base.OI_CHANGE_LOOKBACK,
            "oi_level_window": base.OI_LEVEL_WINDOW,
            "price_mom_lookback": base.PRICE_MOM_LOOKBACK,
            "funding": "dropped (tie degeneracy)" if not funding_usable else "usable",
            "decile_frac": base.DECILE_FRAC,
            "robustness_hold5_nonoverlapping": True,
        }
        param_hash = hashlib.sha256(
            json.dumps(param_dict, sort_keys=True).encode()).hexdigest()

        result = {
            "construction": param_dict["construction"],
            "cost_model": "corrected",
            "factors": factor_lists[name],
            "composite": name,
            "decision_cost_bps_both_legs": DECISION_COST_BPS,
            "cost_bps_both_legs_maker_blend": round(COST_MAKER_BLEND_BPS, 4),
            "cost_bps_both_legs_fee_source": round(COST_FEE_SOURCE_BPS, 4),
            "cost_bps_both_legs_conservative": round(COST_CONSERVATIVE_BPS, 4),
            "no_lookahead": True, "leverage": "none_+_/-1x_spread", "live": "off",
            "data_source": "hl_oi_hf parquet (native perps, mark_price)",
            "n_coins_universe": n_coins,
            "funding_usable": funding_usable,
            "hold_1d": results_by_composite[name][HOLD_PRIMARY],
            "hold_5d": results_by_composite[name][HOLD_5D],
        }

        if not args.no_write:
            e = ledger.increment_trial("HYP-21", param_hash, universe_hash,
                                       period_start, period_end, result)
            print(f"\n  wrote trial {name}: param_hash={e['param_hash'][:16]}...  "
                  f"chain_hash={e['chain_hash'][:16]}...")
        else:
            print(f"\n  [--no-write] {name}: param_hash={param_hash[:16]}...")

    print("\nDone.")
    return 0


if __name__ == "__main__":
    sys.exit(main())