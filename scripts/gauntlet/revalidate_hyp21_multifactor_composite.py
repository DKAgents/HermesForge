"""revalidate_hyp21_multifactor_composite.py — HYP-21 multi-factor cross-sectional
positioning composite.

Read-only research driver. Builds on HYP-20's validated-but-weak single factor
(cross-sectional 7d OI log-change, +11-13 bps gross, independent of price, but
erased by turnover cost). Question: does a COMPOSITE of independent positioning
dimensions clear the 45bps both-legs hurdle where the single factor could not?

Pre-registered (FIXED — no post-hoc tuning):

  Factors (each cross-sectionally z-scored DAILY):
    1. OI-change     = trailing 7d OI % (log) change.
    2. OI-level      = OI vs its own trailing 90d mean z-score
                       (time-series z, then cross-sectionally z-scored).
    3. Funding       = current funding rate rank — DROPPED (still degenerate:
                       ~57% of cells pinned at HL default rate; see HYP-20 §3).
    4. Price-mom 7d  = trailing 7d price log change (CONTROL factor).

  Composites (both pre-committed, reported separately):
    - C-positioning  = z(OI-change) + z(OI-level)            (no price, no funding)
    - C-all          = C-positioning + z(price-momentum)

  Long top-decile / short bottom-decile, equal weight, daily rebalance; 5d hold
  reported separately. Next-open fill both sides; signal at close[t] uses data
  through day t only (no look-ahead). Cost 45bps/leg fail-closed taker charged to
  BOTH legs (90bps round trip); fee_source realistic (24bps) cross-check. No
  leverage beyond ±1x spread. LIVE off. Reconcile total R == by-trade R.

Writes ONE trials-ledger entry per composite (C-positioning, C-all) with a FRESH
param_hash.

Usage: python3 revalidate_hyp21_multifactor_composite.py [--no-write]
"""

from __future__ import annotations

import argparse
import glob
import hashlib
import json
import pathlib
import sqlite3
import sys

import numpy as np
import pandas as pd

_THIS_DIR = pathlib.Path(__file__).resolve().parent          # scripts/gauntlet
for _p in (_THIS_DIR, str(_THIS_DIR.parent)):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import trials_ledger as ledger                              # noqa: E402
from fee_source import get_round_trip_bps, get_taker_bps    # noqa: E402

OI_DIR = pathlib.Path.home() / ".hermes" / "market_data" / "hl_oi_hf"
FUNDING_DB = pathlib.Path.home() / ".hermes" / "market_data" / "hl_funding" / "funding.db"

# ── Pre-registered constants (FIXED) ────────────────────────────────────────
OI_CHANGE_LOOKBACK = 7          # factor 1 window (matches HYP-20 H1)
OI_LEVEL_WINDOW = 90            # factor 2 trailing window (time-series z)
PRICE_MOM_LOOKBACK = 7          # factor 4 window (control)
DECILE_FRAC = 0.10              # top/bottom decile
MIN_COINS_DAY = 20              # require >= this many ranked coins to form a day
COST_HURDLE_BPS_LEG = 45.0      # fail-closed taker, per leg (both legs charged)
HOLD_PRIMARY = 1                # daily rebalance (primary)
HOLD_5D = 5                     # 5d holding (turnover-sensitivity report)


# ────────────────────────────────────────────────────────────────────────────
def load_oi_daily() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load native-perp hourly OI -> daily wide panels (open, close, oi).

    Returns (opens, closes, ois): each a date-indexed DataFrame, columns=coins,
    values aligned to a full daily calendar (NaN where a coin had no bar).
    """
    files = sorted(glob.glob(str(OI_DIR / "*.parquet")))
    if not files:
        raise SystemExit(f"no parquet under {OI_DIR}")
    cols = ["timestamp", "coin", "dex", "mark_price", "open_interest"]
    parts = [pd.read_parquet(f, columns=cols) for f in files]
    df = pd.concat(parts, ignore_index=True)
    native = df[df["dex"] == ""].dropna(subset=["mark_price", "open_interest"])
    native["date"] = native["timestamp"].dt.normalize()

    daily = (native.sort_values("timestamp")
             .groupby(["coin", "date"], sort=False)
             .agg(open=("mark_price", "first"),
                  close=("mark_price", "last"),
                  oi=("open_interest", "last"))
             .reset_index())

    start = daily["date"].min()
    end = daily["date"].max()
    cal = pd.date_range(start, end, freq="D", tz="UTC")

    opens = daily.pivot(index="date", columns="coin", values="open").reindex(cal)
    closes = daily.pivot(index="date", columns="coin", values="close").reindex(cal)
    ois = daily.pivot(index="date", columns="coin", values="oi").reindex(cal)
    return opens, closes, ois


def funding_degeneracy() -> tuple[float, float]:
    """Return (frac_cells_at_modal, modal_rate) for the funding store."""
    con = sqlite3.connect(FUNDING_DB)
    df = pd.read_sql_query("SELECT funding_rate FROM funding", con)
    con.close()
    fr = df["funding_rate"].to_numpy(dtype=float)
    fr = fr[np.isfinite(fr)]
    modal = float(pd.Series(fr).mode().iloc[0])
    frac = float((np.abs(fr - modal) < 1e-12).mean())
    return frac, modal


def xs_zscore(frame: pd.DataFrame) -> pd.DataFrame:
    """Cross-sectional z-score: per row (day), (x - mean)/std across coins."""
    mu = frame.mean(axis=1)
    sd = frame.std(axis=1).replace(0.0, np.nan)
    return frame.sub(mu, axis=0).div(sd, axis=0)


# ────────────────────────────────────────────────────────────────────────────
def cross_sectional_spread(signal_frame: pd.DataFrame, opens: pd.DataFrame,
                           hold: int, cost_per_round_trip: float,
                           label: str) -> dict:
    """Rank coins cross-sectionally each day; long top-decile, short bottom-decile.

    Returns a dict of summary metrics + per-rebalance records. (Identical to the
    HYP-20 engine — deterministic decile split of a composite score is the same
    operation whether the score is a raw factor or an equal-weight z-sum.)
    """
    sig = signal_frame
    cols = [c for c in sig.columns if c in opens.columns]
    sig = sig[cols]
    opens_sub = opens[cols]
    entry = opens_sub.shift(-1)
    exitp = opens_sub.shift(-(1 + hold))
    fwd = exitp / entry - 1.0

    common = sig.index.intersection(opens_sub.index)
    sig = sig.loc[common]
    fwd = fwd.loc[common]

    records = []
    long_contribs = []
    short_contribs = []
    n_coins_list = []

    dates = list(sig.index)
    for t in range(len(dates) - (1 + hold)):
        s = sig.iloc[t].to_numpy(dtype=float)
        f = fwd.iloc[t].to_numpy(dtype=float)
        mask = np.isfinite(s) & np.isfinite(f)
        if mask.sum() < MIN_COINS_DAY:
            continue
        s_v = s[mask]; f_v = f[mask]
        order = np.argsort(s_v)
        n = len(s_v)
        k = max(1, n // 10)
        bot_idx = order[:k]
        top_idx = order[-k:]
        long_ret = float(np.mean(f_v[top_idx]))
        short_ret = float(np.mean(f_v[bot_idx]))
        gross = long_ret - short_ret
        net = gross - cost_per_round_trip
        records.append({"date": dates[t], "n": n, "k": k,
                        "long_ret": long_ret, "short_ret": short_ret,
                        "gross": gross, "net": net})
        long_contribs.append(long_ret)
        short_contribs.append(short_ret)
        n_coins_list.append(n)

    if not records:
        return {"label": label, "hold": hold, "n_rebalances": 0,
                "reconciled": False, "records": []}

    gross_arr = np.array([r["gross"] for r in records])
    net_arr = np.array([r["net"] for r in records])

    total_r_series = float(net_arr.sum())
    total_gross_series = float(gross_arr.sum())
    by_trade_long = float(np.sum(long_contribs))
    by_trade_short = float(np.sum(short_contribs))
    by_trade_gross = by_trade_long - by_trade_short
    by_trade_net = by_trade_gross - cost_per_round_trip * len(records)
    reconciled = abs(total_r_series - by_trade_net) < 1e-9 and \
                 abs(total_gross_series - by_trade_gross) < 1e-9

    n_days = len(records)
    mean_gross = float(gross_arr.mean())
    mean_net = float(net_arr.mean())
    sharpe = float(mean_net / net_arr.std()) if net_arr.std() > 0 else 0.0
    wins = float((net_arr > 0).mean())

    return {
        "label": label, "hold": hold, "n_rebalances": n_days,
        "mean_n_coins": float(np.mean(n_coins_list)),
        "mean_k_per_leg": float(np.mean([r["k"] for r in records])),
        "mean_gross_r": mean_gross, "mean_gross_bps": mean_gross * 1e4,
        "mean_net_r": mean_net, "mean_net_bps": mean_net * 1e4,
        "cost_per_round_trip_bps": cost_per_round_trip * 1e4,
        "total_r_series": total_r_series,
        "total_gross_series": total_gross_series,
        "by_trade_gross": by_trade_gross, "by_trade_net": by_trade_net,
        "reconciled": bool(reconciled),
        "sharpe": sharpe, "win_rate": wins,
        "sign": "momentum" if mean_gross > 0 else "reversal",
        "annualized_gross_bps": mean_gross * 1e4 * (365.0 / hold),
        "records": records,
    }


def daily_xs_corr(a: pd.DataFrame, b: pd.DataFrame) -> float:
    """Mean daily cross-sectional Pearson corr (pooled over days, skip NaN)."""
    common = a.index.intersection(b.index)
    cc = list(set(a.columns) & set(b.columns))
    a = a.loc[common, cc]; b = b.loc[common, cc]
    ranks = []
    for d in common:
        av = a.loc[d].to_numpy(dtype=float)
        bv = b.loc[d].to_numpy(dtype=float)
        m = np.isfinite(av) & np.isfinite(bv)
        if m.sum() < MIN_COINS_DAY:
            continue
        c = np.corrcoef(av[m], bv[m])[0, 1]
        if np.isfinite(c):
            ranks.append(c)
    return float(np.mean(ranks)) if ranks else float("nan")


def _summary(res: dict) -> dict:
    return {
        "n_rebalances": res["n_rebalances"],
        "mean_n_coins": round(res.get("mean_n_coins", 0), 2),
        "mean_k_per_leg": round(res.get("mean_k_per_leg", 0), 2),
        "mean_gross_bps": round(res.get("mean_gross_bps", 0.0), 4),
        "sign": res.get("sign", ""),
        "mean_net_bps_hurdle": round(res.get("mean_net_bps", 0.0), 4),
        "sharpe": round(res.get("sharpe", 0.0), 6),
        "win_rate": round(res.get("win_rate", 0.0), 6),
        "total_r_series": round(res.get("total_r_series", 0.0), 8),
        "total_gross_series": round(res.get("total_gross_series", 0.0), 8),
        "by_trade_net": round(res.get("by_trade_net", 0.0), 8),
        "reconciled": res.get("reconciled", False),
    }


# ────────────────────────────────────────────────────────────────────────────
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-write", action="store_true")
    args = ap.parse_args()

    taker_bps = get_taker_bps("crypto")
    rtb_bps = get_round_trip_bps("crypto")
    cost_hurdle = 2 * COST_HURDLE_BPS_LEG / 1e4          # 90 bps both legs
    cost_real = 2 * rtb_bps / 1e4                        # 24 bps both legs

    print("=== HYP-21 multi-factor cross-sectional positioning composite ===\n")
    print(f"cost model: hurdle {COST_HURDLE_BPS_LEG:.0f}bps/leg x2 = "
          f"{cost_hurdle*1e4:.0f}bps/round-trip (fail-closed taker); "
          f"fee_source realistic = {cost_real*1e4:.0f}bps/round-trip")

    # ── funding degeneracy check (factor 3 drop decision) ───────────────────
    frac_modal, modal = funding_degeneracy()
    print(f"\nfactor 3 (funding): store modal rate={modal:.8f}/hr  "
          f"{frac_modal*100:.1f}% of cells at modal (HL default)")
    if frac_modal > 0.50:
        print(f"  -> 57%+ tie degeneracy persists (HYP-20 flagged it). "
              f"DROPPING funding factor per pre-registration.")
        funding_usable = False
    else:
        print("  funding usable -> would include z(funding) (did not trigger).")
        funding_usable = True

    # ── load OI panels ──────────────────────────────────────────────────────
    print("\nloading native-perp hourly OI -> daily panels ...")
    opens, closes, ois = load_oi_daily()
    n_coins = opens.shape[1]
    print(f"  OI panel: {opens.shape[0]} days x {n_coins} native coins "
          f"({opens.index.min().date()} -> {opens.index.max().date()})")

    oi_log = np.log(ois.replace(0.0, np.nan))
    close_log = np.log(closes.replace(0.0, np.nan))

    # ── factor 1: OI-change (7d log change) ─────────────────────────────────
    f_oi_change = oi_log - oi_log.shift(OI_CHANGE_LOOKBACK)

    # ── factor 2: OI-level (time-series z vs trailing 90d, then xs-z) ───────
    # trailing 90d baseline EXCLUDES the current day (prev 90 days) so the
    # current OI is not self-included in its own mean/std.
    oi_mean90 = ois.shift(1).rolling(OI_LEVEL_WINDOW,
                                     min_periods=OI_LEVEL_WINDOW).mean()
    oi_std90 = ois.shift(1).rolling(OI_LEVEL_WINDOW,
                                    min_periods=OI_LEVEL_WINDOW).std()
    f_oi_level_ts = (ois - oi_mean90) / oi_std90.replace(0.0, np.nan)

    # ── factor 4: price momentum (7d log change, CONTROL) ───────────────────
    f_price_mom = close_log - close_log.shift(PRICE_MOM_LOOKBACK)

    # ── cross-sectionally z-score each factor (daily) ───────────────────────
    z_oi_change = xs_zscore(f_oi_change)
    z_oi_level = xs_zscore(f_oi_level_ts)
    z_price_mom = xs_zscore(f_price_mom)

    # ── composites (pre-committed, equal-weight z-sum) ──────────────────────
    c_positioning = z_oi_change + z_oi_level          # no funding, no price
    c_all = c_positioning + z_price_mom               # + price momentum

    print("\nfactor cross-sectional cross-correlations (mean daily, pooled):")
    print(f"  corr(z(OI-change), z(price-mom)) = "
          f"{daily_xs_corr(z_oi_change, z_price_mom):+.3f}")
    print(f"  corr(z(OI-change), z(OI-level))  = "
          f"{daily_xs_corr(z_oi_change, z_oi_level):+.3f}")
    print(f"  corr(z(OI-level),  z(price-mom)) = "
          f"{daily_xs_corr(z_oi_level, z_price_mom):+.3f}")

    # ── evaluate composites + single factors ────────────────────────────────
    def _run(name, sig):
        out = {}
        for hold in (HOLD_PRIMARY, HOLD_5D):
            r = cross_sectional_spread(sig, opens, hold, cost_hurdle,
                                       f"{name}-hold{hold}")
            rr = cross_sectional_spread(sig, opens, hold, cost_real,
                                        f"{name}-hold{hold}-real")
            out[hold] = (r, rr)
        return out

    print("\n===== single-factor baselines (hold=1d) =====")
    singles = {
        "OI-change(7d)": z_oi_change,
        "OI-level(90d)": z_oi_level,
        "price-mom(7d)": z_price_mom,
    }
    single_res = {}
    for name, sig in singles.items():
        r, rr = _run(name, sig)[HOLD_PRIMARY]
        single_res[name] = (r, rr)
        print(f"  {name:16s} gross {r['mean_gross_bps']:+.3f} bps/reb  "
              f"net@hurdle {r['mean_net_bps']:+.3f}  "
              f"net@fee_source {rr['mean_net_bps']:+.3f}  "
              f"n={r['n_rebalances']}  recon={r['reconciled']}")

    print("\n===== composites =====")
    composites = {
        "C-positioning": c_positioning,     # z(OI-change) + z(OI-level)
        "C-all": c_all,                     # + z(price-mom)
    }
    comp_res = {}
    for name, sig in composites.items():
        comp_res[name] = {}
        for hold in (HOLD_PRIMARY, HOLD_5D):
            r, rr = _run(name, sig)[hold]
            comp_res[name][hold] = (r, rr)
            print(f"  {name:14s} hold={hold}d: gross {r['mean_gross_bps']:+.3f} "
                  f"bps/reb (ann {r['annualized_gross_bps']:+.1f})  "
                  f"sign={r['sign']}")
            print(f"    {'':14s} net@hurdle {r['mean_net_bps']:+.3f} bps/reb  "
                  f"net@fee_source {rr['mean_net_bps']:+.3f}  "
                  f"sharpe {r['sharpe']:+.3f}  "
                  f"n_rebal={r['n_rebalances']}  "
                  f"mean_k/leg={r['mean_k_per_leg']:.1f}  recon={r['reconciled']}")

    # ── write trials (one per composite) ────────────────────────────────────
    period_start = str(opens.index.min().date())
    period_end = str(opens.index.max().date())
    universe = sorted(opens.columns.tolist())
    universe_hash = hashlib.sha256(",".join(universe).encode()).hexdigest()

    factor_spec = {
        "oi_change_lookback": OI_CHANGE_LOOKBACK,
        "oi_level_window": OI_LEVEL_WINDOW,
        "price_mom_lookback": PRICE_MOM_LOOKBACK,
        "funding": "dropped (57%+ tie degeneracy at HL default)",
        "z_score": "cross_sectional_daily",
        "composite_build": "equal_weight_sum_of_z_scores",
    }

    def _write(label: str, param_dict: dict, res: dict) -> None:
        param_hash = hashlib.sha256(
            json.dumps(param_dict, sort_keys=True).encode()).hexdigest()
        result = {
            "construction": "multifactor_cross_sectional_composite",
            "factors": param_dict["factors"],
            "composite": param_dict["composite"],
            "cost_bps_both_legs_hurdle": cost_hurdle * 1e4,
            "cost_bps_both_legs_fee_source": cost_real * 1e4,
            "min_coins_day": MIN_COINS_DAY,
            "decile_frac": DECILE_FRAC,
            "no_lookahead": True, "leverage": "none_+_/-1x_spread", "live": "off",
            "data_source": "hl_oi_hf parquet (native perps, mark_price)",
            "n_coins_universe": n_coins,
            "funding_usable": funding_usable,
            "hold_1d": _summary(res[HOLD_PRIMARY][0]),
            "hold_1d_net_fee_source_bps": round(
                res[HOLD_PRIMARY][1]["mean_net_bps"], 4),
            "hold_5d": _summary(res[HOLD_5D][0]),
            "hold_5d_net_fee_source_bps": round(
                res[HOLD_5D][1]["mean_net_bps"], 4),
        }
        if not args.no_write:
            e = ledger.increment_trial("HYP-21", param_hash, universe_hash,
                                       period_start, period_end, result)
            print(f"\n  wrote trial {label}: param_hash={e['param_hash'][:16]}...  "
                  f"chain_hash={e['chain_hash'][:16]}...")
        else:
            print(f"\n  [--no-write] {label}: param_hash={param_hash[:16]}...")

    _write("C-positioning",
           {"composite": "C-positioning",
            "factors": ["oi_change_7d", "oi_level_90d"]},
           comp_res["C-positioning"])
    _write("C-all",
           {"composite": "C-all",
            "factors": ["oi_change_7d", "oi_level_90d", "price_mom_7d"]},
           comp_res["C-all"])

    print("\nDone.")
    return 0


if __name__ == "__main__":
    sys.exit(main())