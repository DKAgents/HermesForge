"""revalidate_hyp20_cross_sectional_oi.py — HYP-20 cross-sectional OI/funding momentum.

Read-only research driver. Tests the UNTESTED question HYP-16 could not ask:
does a coin's OI (positioning) RELATIVE TO OTHER COINS *right now* predict its
RELATIVE future return? Cross-sectional (relative-value) ranking, NOT the
time-series OI test HYP-16 already falsified.

Pre-registered operationalization (FIXED — no post-hoc tuning):
  * Universe: native HL perps (dex == ''). Hourly OI+mark -> daily per coin
    (OI = last hourly reading, close = last mark, open = first mark).
  * H1 (primary): cross-sectional rank of trailing 7d OI log change. Long
    top-decile, short bottom-decile, equal-weight, rebalanced daily. Also
    report 5d holding to show cost-sensitivity to turnover.
  * V-A (pre-committed variant): 7d -> 30d OI log change (slower signal).
  * H2 (secondary): cross-sectional rank of current funding rate, BOTH
    directions (continuation AND fade) — the winning direction is reported,
    not assumed. Funding store = hl_funding/funding.db (35 coins, ~404d).
  * Fill: next-open entry (signal at close[t] uses OI through day t;
    enter open[t+1]; exit open[t+1+hold] at next rebalance). No look-ahead.
  * Cost: 45bps fail-closed taker charged to BOTH legs (long + short of the
    spread). Per-leg 45bps = repo's pre-registered "4x" conservative hurdle
    (matching HYP-16 COST_BPS_FAIL_CLOSED). fee_source round-trip (12bps) is
    reported separately as the realistic cross-check, charged once.
  * No leverage beyond the ±1x long/short spread. LIVE off.

Writes ONE trials-ledger entry per (H1, V-A, H2) with a FRESH param_hash.

Usage: python3 revalidate_hyp20_cross_sectional_oi.py [--no-write]
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
H1_LOOKBACK_DAYS = 7            # H1 signal window
VA_LOOKBACK_DAYS = 30           # V-A signal window
DECILE_FRAC = 0.10              # top/bottom decile
MIN_COINS_DAY = 20              # require >= this many ranked coins to form a day
COST_HURDLE_BPS_LEG = 45.0      # fail-closed taker, per leg (both legs charged)
HOLD_PRIMARY = 1                # daily rebalance (primary)
HOLD_5D = 5                     # 5d holding (turnover-sensitivity report)
FUNDING_MIN_DAYS = 200          # H2 data-gate floor (~200d usable)


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


def load_funding_daily() -> pd.DataFrame:
    """Funding rate hourly -> daily wide panel (last hourly rate per coin)."""
    con = sqlite3.connect(FUNDING_DB)
    q = ("SELECT coin, time, funding_rate FROM funding ORDER BY time ASC")
    df = pd.read_sql_query(q, con)
    con.close()
    df["date"] = pd.to_datetime(df["time"], unit="ms", utc=True).dt.normalize()
    daily = (df.sort_values("time").groupby(["coin", "date"], sort=False)
             .agg(funding=("funding_rate", "last")).reset_index())
    start = daily["date"].min(); end = daily["date"].max()
    cal = pd.date_range(start, end, freq="D", tz="UTC")
    return daily.pivot(index="date", columns="coin", values="funding").reindex(cal)


# ────────────────────────────────────────────────────────────────────────────
def cross_sectional_spread(signal_frame: pd.DataFrame, opens: pd.DataFrame,
                           hold: int, cost_per_round_trip: float,
                           label: str) -> dict:
    """Rank coins cross-sectionally each day; long top-decile, short bottom-decile.

    signal_frame: date x coin signal values (7d/30d OI log change, or funding).
    opens:        date x coin daily open (for next-open fill returns).
    hold:         holding horizon in days (1=primary daily, 5=5d).
    cost_per_round_trip: fee in return-fraction (e.g. 0.0090 for 90bps) per
        rebalance, charged once (both legs), subtracted from the gross spread.

    Returns a dict of summary metrics + per-rebalance records.
    """
    sig = signal_frame
    # align columns to coins present in BOTH the signal and the price panel
    cols = [c for c in sig.columns if c in opens.columns]
    sig = sig[cols]
    opens_sub = opens[cols]
    # forward return: enter open[t+1], exit open[t+1+hold] (next-open both sides)
    entry = opens_sub.shift(-1)
    exitp = opens_sub.shift(-(1 + hold))
    fwd = exitp / entry - 1.0

    common = sig.index.intersection(opens_sub.index)
    sig = sig.loc[common]
    fwd = fwd.loc[common]

    records = []          # per-rebalance (day) spread
    long_contribs = []    # per-position signed return (for by-trade recon)
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
        order = np.argsort(s_v)                    # ascending
        n = len(s_v)
        k = max(1, n // 10)                        # decile size (floor 10%)
        bot_idx = order[:k]                        # lowest signal -> short
        top_idx = order[-k:]                       # highest signal -> long
        long_ret = float(np.mean(f_v[top_idx]))
        short_ret = float(np.mean(f_v[bot_idx]))
        gross = long_ret - short_ret
        net = gross - cost_per_round_trip
        records.append({
            "date": dates[t], "n": n, "k": k,
            "long_ret": long_ret, "short_ret": short_ret,
            "gross": gross, "net": net,
        })
        long_contribs.append(long_ret)
        short_contribs.append(short_ret)
        n_coins_list.append(n)

    if not records:
        return _empty_result(label, hold)

    gross_arr = np.array([r["gross"] for r in records])
    net_arr = np.array([r["net"] for r in records])

    # ── reconcile total R == by-trade R ─────────────────────────────────────
    # time-series: sum of daily net spread (net = gross - cost, cost once/day)
    total_r_series = float(net_arr.sum())
    total_gross_series = float(gross_arr.sum())
    # by-trade: sum of (long leg) + (short leg) = gross; subtract cost ONCE
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


def _empty_result(label: str, hold: int) -> dict:
    return {"label": label, "hold": hold, "n_rebalances": 0, "reconciled": False,
            "records": []}


def _pf(r_net: np.ndarray) -> float:
    gains = r_net[r_net > 0].sum()
    losses = abs(r_net[r_net < 0].sum())
    return float(gains / losses) if losses > 0 else (float("inf") if gains > 0 else 0.0)


# ────────────────────────────────────────────────────────────────────────────
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-write", action="store_true")
    args = ap.parse_args()

    taker_bps = get_taker_bps("crypto")
    rtb_bps = get_round_trip_bps("crypto")
    cost_hurdle = 2 * COST_HURDLE_BPS_LEG / 1e4          # 90 bps both legs
    cost_real = 2 * rtb_bps / 1e4                        # 24 bps both legs (fee_source)

    print("=== HYP-20 cross-sectional OI/funding momentum (RELATIVE ranking) ===\n")
    print(f"cost model: hurdle {COST_HURDLE_BPS_LEG:.0f}bps/leg x2 = "
          f"{cost_hurdle*1e4:.0f}bps/round-trip (fail-closed); "
          f"fee_source realistic = {cost_real*1e4:.0f}bps/round-trip")

    print("\nloading native-perp hourly OI -> daily panels ...")
    opens, closes, ois = load_oi_daily()
    n_coins = opens.shape[1]
    print(f"  OI panel: {opens.shape[0]} days x {n_coins} native coins "
          f"({opens.index.min().date()} -> {opens.index.max().date()})")

    oi_log = np.log(ois.replace(0.0, np.nan))

    # ── H1 (7d) and V-A (30d) OI log-change signals ─────────────────────────
    sig_h1 = oi_log.diff(H1_LOOKBACK_DAYS)
    sig_va = oi_log.diff(VA_LOOKBACK_DAYS)

    results = {}

    for name, sig, lb in [("H1", sig_h1, H1_LOOKBACK_DAYS),
                          ("V-A", sig_va, VA_LOOKBACK_DAYS)]:
        print(f"\n===== {name} — cross-sectional {lb}d OI log-change rank =====")
        for hold in (HOLD_PRIMARY, HOLD_5D):
            r = cross_sectional_spread(sig, opens, hold, cost_hurdle,
                                       f"{name}-{lb}d-hold{hold}")
            results[f"{name}_hold{hold}"] = r
            print(f"  hold={hold}d: n_rebal={r['n_rebalances']}  "
                  f"mean n_coins={r['mean_n_coins']:.0f}  k/leg={r['mean_k_per_leg']:.1f}")
            print(f"    gross {r['mean_gross_bps']:+.3f} bps/reb "
                  f"(ann {r['annualized_gross_bps']:+.1f} bps)  sign={r['sign']}")
            print(f"    net@hurdle {r['mean_net_bps']:+.3f} bps/reb   "
                  f"sharpe {r['sharpe']:+.3f}  win {r['win_rate']:.3f}")
            # fee_source realistic cross-check
            rr = cross_sectional_spread(sig, opens, hold, cost_real,
                                        f"{name}-{lb}d-hold{hold}-real")
            print(f"    net@fee_source {rr['mean_net_bps']:+.3f} bps/reb")
            print(f"    reconcile totalR==byTrade: {r['reconciled']}  "
                  f"(series {r['total_r_series']:.6f} vs byTrade {r['by_trade_net']:.6f})")
            results[f"{name}_hold{hold}_real"] = rr

    # ── H2 (funding) ─────────────────────────────────────────────────────────
    print("\n===== H2 — cross-sectional funding rank (both directions) =====")
    funding_daily = load_funding_daily()
    fspan = (funding_daily.index.max() - funding_daily.index.min()).days
    fcoins = funding_daily.shape[1]
    print(f"  funding panel: {funding_daily.shape[0]} days x {fcoins} coins "
          f"(span {fspan}d)")
    overlap = sorted(set(funding_daily.columns) & set(opens.columns))
    print(f"  funding coins with OI price data: {len(overlap)}/{fcoins}")

    if fspan < FUNDING_MIN_DAYS:
        print(f"  FUNDING SPAN {fspan}d < {FUNDING_MIN_DAYS}d -> H2 DATA-GATED")
        h2_status = "DATA-GATED"
        h2_result = {"h2_status": "DATA-GATED",
                     "funding_span_days": int(fspan), "coins": fcoins}
    else:
        h2_status = "RUN"
        sig_fund = funding_daily.astype(float)

        # Tie-degeneracy diagnostic: funding is heavily quantized to HL's
        # default rate, so cross-sectional rank is dominated by ties.
        fvals = sig_fund.to_numpy(dtype=float).ravel()
        fvals = fvals[np.isfinite(fvals)]
        modal = float(pd.Series(fvals).mode().iloc[0])
        frac_at_modal = float((np.abs(fvals - modal) < 1e-12).mean())
        print(f"  funding tie-degeneracy: modal rate={modal:.8f}, "
              f"{frac_at_modal*100:.1f}% of finite cells = modal (default) rate")

        # continuation: rank by funding, long top-decile, short bottom-decile.
        # fade is the EXACT mirror (swap legs) of the same deterministic
        # ranking — so fade_gross == -continuation_gross by construction.
        r_cont = cross_sectional_spread(sig_fund, opens, HOLD_PRIMARY,
                                        cost_hurdle, "H2-continuation")
        r_cont_real = cross_sectional_spread(sig_fund, opens, HOLD_PRIMARY,
                                             cost_real, "H2-continuation-real")
        fade_gross_bps = -r_cont["mean_gross_bps"]
        fade_net_hurdle_bps = fade_gross_bps - cost_hurdle * 1e4
        fade_net_real_bps = fade_gross_bps - cost_real * 1e4
        print(f"  funding span {fspan}d x {fcoins} coins (usable, >200d gate PASS)")
        print(f"  continuation: n_rebal={r_cont['n_rebalances']}  "
              f"gross {r_cont['mean_gross_bps']:+.3f} bps/reb  "
              f"net@hurdle {r_cont['mean_net_bps']:+.3f} bps  "
              f"net@fee_source {r_cont_real['mean_net_bps']:+.3f} bps  "
              f"recon={r_cont['reconciled']}")
        print(f"  fade (mirror): gross {fade_gross_bps:+.3f} bps/reb  "
              f"net@hurdle {fade_net_hurdle_bps:+.3f} bps  "
              f"net@fee_source {fade_net_real_bps:+.3f} bps")
        direction = ("momentum/continuation" if r_cont["mean_gross_bps"] > 0
                     else "fade/reversal")
        print(f"  winning direction (gross): {direction}  "
              f"(high funding -> relative {'out' if r_cont['mean_gross_bps']>0 else 'under'}performance)")

        h2_result = {
            "h2_status": "RUN",
            "funding_span_days": int(fspan),
            "funding_coins": fcoins,
            "overlap_coins": len(overlap),
            "modal_funding_rate": modal,
            "frac_cells_at_modal": frac_at_modal,
            "continuation_n_rebalances": r_cont["n_rebalances"],
            "continuation_mean_gross_bps": round(r_cont["mean_gross_bps"], 4),
            "continuation_mean_net_hurdle_bps": round(r_cont["mean_net_bps"], 4),
            "continuation_mean_net_real_bps": round(r_cont_real["mean_net_bps"], 4),
            "continuation_total_r_series": round(r_cont["total_r_series"], 8),
            "continuation_by_trade_net": round(r_cont["by_trade_net"], 8),
            "continuation_reconciled": r_cont["reconciled"],
            "fade_mean_gross_bps": round(fade_gross_bps, 4),
            "fade_mean_net_hurdle_bps": round(fade_net_hurdle_bps, 4),
            "fade_mean_net_real_bps": round(fade_net_real_bps, 4),
            "winning_direction": direction,
        }

    # ── write trials (one per H1/V-A/H2) ────────────────────────────────────
    period_start = str(opens.index.min().date())
    period_end = str(opens.index.max().date())
    universe = sorted(opens.columns.tolist())
    universe_hash = hashlib.sha256(",".join(universe).encode()).hexdigest()

    def _write(label: str, param_dict: dict, res: dict) -> None:
        param_hash = hashlib.sha256(
            json.dumps(param_dict, sort_keys=True).encode()).hexdigest()
        result = {
            "construction": "cross_sectional_oi_momentum",
            "signal": param_dict["signal"],
            "hold_days": param_dict.get("hold_days"),
            "cost_bps_both_legs_hurdle": cost_hurdle * 1e4,
            "cost_bps_both_legs_fee_source": cost_real * 1e4,
            "min_coins_day": MIN_COINS_DAY,
            "decile_frac": DECILE_FRAC,
            "no_lookahead": True, "leverage": "none_+_/-1x_spread", "live": "off",
            "data_source": "hl_oi_hf parquet (native perps, mark_price)",
            "n_coins_universe": n_coins,
        }
        if res.get("h2_status"):
            result.update({k: v for k, v in res.items()
                           if k not in ("directions", "h2_status")})
            result["h2_status"] = res["h2_status"]
        else:
            result.update({
                "n_rebalances": res["n_rebalances"],
                "mean_n_coins": round(res["mean_n_coins"], 2),
                "mean_k_per_leg": round(res["mean_k_per_leg"], 2),
                "mean_gross_bps": round(res["mean_gross_bps"], 4),
                "mean_net_bps_hurdle": round(res["mean_net_bps"], 4),
                "sign": res["sign"],
                "sharpe": round(res["sharpe"], 6),
                "win_rate": round(res["win_rate"], 6),
                "total_r_series": round(res["total_r_series"], 8),
                "total_gross_series": round(res["total_gross_series"], 8),
                "by_trade_net": round(res["by_trade_net"], 8),
                "reconciled": res["reconciled"],
            })
        if not args.no_write:
            e = ledger.increment_trial("HYP-20", param_hash, universe_hash,
                                       period_start, period_end, result)
            print(f"  wrote trial {label}: param_hash={e['param_hash'][:16]}...  "
                  f"chain_hash={e['chain_hash'][:16]}...")
        else:
            print(f"  [--no-write] {label}: param_hash={param_hash[:16]}...")

    _write("H1", {"signal": f"oi_log_diff_{H1_LOOKBACK_DAYS}d",
                  "hold_days": HOLD_PRIMARY,
                  "direction": "long_top_decile_short_bottom_decile"},
           results["H1_hold1"])
    _write("V-A", {"signal": f"oi_log_diff_{VA_LOOKBACK_DAYS}d",
                   "hold_days": HOLD_PRIMARY,
                   "direction": "long_top_decile_short_bottom_decile"},
           results["V-A_hold1"])
    _write("H2", {"signal": "current_funding_rate_rank", "hold_days": HOLD_PRIMARY,
                  "direction": "both_continuation_and_fade"},
           h2_result)

    print("\nDone.")
    return 0


if __name__ == "__main__":
    sys.exit(main())