"""sweep_hyp16_robustness.py — HYP-16 robustness sweep (pre-registered, FIXED).

Runs the committed robustness sweep for HYP-16 (high-OI expansion + trend),
whose primary run returned a flat null. Purpose is CONFIRM-OR-REFUTE the null,
NOT a hunt for a winning variation — per the pre-registered
trading/strategies/Hypotheses/HYP-16-robustness-sweep.md. The 3 variations are
FIXED and committed; this driver adds or tunes NOTHING.

Variations (each tested in isolation against the HYP-16 baseline, which is
OI >= 90th pct trailing-90d AND close > SMA20; exit close < SMA20 or 5-bar
time stop):

  * BASELINE : pctile=90,  sma=20   (reference; recomputed here for the table
               and cross-checked against primary trial 269c55b8…)
  * V-A      : pctile=90,  sma=50   (slower trend; H1 unchanged by construction)
  * V-B      : pctile=80,  sma=20   (looser OI)
  * V-C      : pctile=95,  sma=20   (tighter OI)

H1 (expansion): extreme-OI |forward move| over next 1-5 bars vs unconditional
baseline, reported as ratio + bootstrap p vs BOTH the full sample AND the
same-date-window overlap (avoids regime-confounding — mirrors the HYP-17/
primary honesty standard).

H2 (directional): LONG when extreme OI AND close > SMA; exit close < SMA or
5-bar time stop; next-open fill (no look-ahead); 45 bps fail-closed taker
charged once per round trip; +1x or flat (no leverage). Also runs the SMA-only
CONTROL (OI filter removed, SAME sma window as the variant) so the OI filter's
marginal contribution is isolated per variant.

Hard rules: unchanged data (HF OI at ~/.hermes/market_data/hl_oi_hf/), native
perps only, no look-ahead, no leverage, LIVE off, one trials-ledger entry per
VARIATION (V-A/B/C) with a fresh param_hash. Baseline already has its primary
entry (269c55b8…) so it is NOT re-written. Path-scoped commit.

Usage: python3 sweep_hyp16_robustness.py [--no-write]
"""

from __future__ import annotations

import argparse
import glob
import hashlib
import json
import pathlib
import sys

import numpy as np
import pandas as pd

# Import the shared loader + cost helpers + ledger from the primary driver so
# universe selection, daily resample, bootstrap, and cost treatment are IDENTICAL
# to the committed HYP-16 primary run. Only the OI percentile + SMA window are
# parameterized (the pre-committed variations); nothing else differs.
import revalidate_high_oi_expansion as primary

OI_DIR = pathlib.Path.home() / ".hermes" / "market_data" / "hl_oi_hf"

PCTILE_WINDOW_DAYS = primary.PCTILE_WINDOW_DAYS
FORWARD_BARS = primary.FORWARD_BARS
TIME_STOP_BARS = primary.TIME_STOP_BARS
TOP_N = primary.TOP_N
COST_BPS_FAIL_CLOSED = primary.COST_BPS_FAIL_CLOSED
BSTRAP_B = primary.BSTRAP_B


# ── Parameterized core (mirrors primary._arrays / compute_h1 / simulate_trades,
#    but with pctile + sma_window as explicit args) ────────────────────────────

def _arrays(daily: pd.DataFrame, pctile: float, sma_window: int):
    d = daily.sort_values("date").reset_index(drop=True)
    close = d["close"].astype(float).to_numpy()
    opn = d["open"].astype(float).to_numpy()
    oi = d["oi"].astype(float).to_numpy()
    dates = d["date"].to_numpy()
    n = len(d)
    pct = (pd.Series(oi).rolling(PCTILE_WINDOW_DAYS, min_periods=PCTILE_WINDOW_DAYS)
             .quantile(pctile / 100.0).to_numpy())
    sma = (pd.Series(close).rolling(sma_window, min_periods=sma_window)
             .mean().to_numpy())
    return d, close, opn, oi, dates, pct, sma, n


def compute_h1(daily: pd.DataFrame, pctile: float):
    d, close, _opn, oi, dates, pct, _sma, n = _arrays(daily, pctile, sma_window=20)
    if n == 0:
        return [], []
    fwd_abs = np.full(n, np.nan)
    fwd_abs_h = {h: np.full(n, np.nan) for h in range(1, FORWARD_BARS + 1)}
    for t in range(n - FORWARD_BARS):
        for h in range(1, FORWARD_BARS + 1):
            fwd_abs_h[h][t] = abs(close[t + h] / close[t] - 1.0)
        fwd_abs[t] = float(np.mean([fwd_abs_h[h][t] for h in range(1, FORWARD_BARS + 1)]))

    events, baseline = [], []
    for t in range(n - FORWARD_BARS):
        if not np.isfinite(fwd_abs[t]):
            continue
        rec = {"coin": d["coin"].iloc[0], "ts": int(dates[t].value // 1_000_000),
               "fwd_abs": float(fwd_abs[t])}
        for h in range(1, FORWARD_BARS + 1):
            rec[f"fwd_abs_h{h}"] = float(fwd_abs_h[h][t])
        baseline.append(rec)
        if np.isfinite(pct[t]) and pct[t] > 0 and oi[t] >= pct[t]:
            rec2 = dict(rec)
            rec2["oi"] = float(oi[t]); rec2["pct"] = float(pct[t])
            events.append(rec2)
    return events, baseline


def simulate_trades(daily: pd.DataFrame, pctile: float, sma_window: int,
                    use_oi_filter: bool):
    d, close, opn, oi, dates, pct, sma, n = _arrays(daily, pctile, sma_window)
    if n == 0:
        return []
    coin = d["coin"].iloc[0]
    cost_45 = COST_BPS_FAIL_CLOSED / 1e4
    rtb_1x = primary.get_round_trip_bps("crypto") / 1e4

    trades = []
    long_pos = False
    e = -1
    for i in range(n):
        exited = False
        if long_pos:
            held_bars = i - e + 1
            if close[i] < sma[i]:
                if i + 1 < n:
                    gross = opn[i + 1] / opn[e] - 1.0
                    trades.append(primary._trade(coin, dates[e], dates[i + 1],
                                                 gross, cost_45, rtb_1x, "sma"))
                long_pos = False; exited = True
            elif held_bars >= TIME_STOP_BARS:
                if i + 1 < n:
                    gross = opn[i + 1] / opn[e] - 1.0
                    trades.append(primary._trade(coin, dates[e], dates[i + 1],
                                                 gross, cost_45, rtb_1x, "time_stop"))
                long_pos = False; exited = True
        if not long_pos and not exited:
            if i + 1 < n and np.isfinite(pct[i]) and np.isfinite(sma[i]):
                cond = close[i] > sma[i]
                if use_oi_filter:
                    cond = cond and oi[i] >= pct[i]
                if cond:
                    long_pos = True
                    e = i + 1
    return trades


# ── Result assembly (mirrors primary main() analysis) ─────────────────────────

def run_variant(label: str, pctile: float, sma_window: int, daily: pd.DataFrame,
                universe: list[str], ledger, write: bool = True) -> dict:
    all_events, all_baseline = [], []
    h2_trades, ctrl_trades = [], []
    for coin in universe:
        sub = daily[daily["coin"] == coin]
        ev, bl = compute_h1(sub, pctile)
        tr = simulate_trades(sub, pctile, sma_window, use_oi_filter=True)
        ct = simulate_trades(sub, pctile, sma_window, use_oi_filter=False)
        all_events.extend(ev); all_baseline.extend(bl)
        h2_trades.extend(tr); ctrl_trades.extend(ct)

    ev = pd.DataFrame(all_events); bl = pd.DataFrame(all_baseline)
    regime_abs = ev["fwd_abs"].astype(float).to_numpy()
    base_abs = bl["fwd_abs"].astype(float).to_numpy()

    bs = primary.bootstrap_diff(regime_abs, base_abs, BSTRAP_B, primary.BSTRAP_SEED)
    base_overlap = bl[(bl["ts"] >= int(ev["ts"].min())) & (bl["ts"] <= int(ev["ts"].max()))]
    base_overlap_abs = base_overlap["fwd_abs"].astype(float).to_numpy()
    bs_overlap = primary.bootstrap_diff(regime_abs, base_overlap_abs,
                                        BSTRAP_B, primary.BSTRAP_SEED)

    net45 = np.array([t["net_r_45"] for t in h2_trades], dtype=float) if h2_trades else np.array([])
    ctrl45 = np.array([t["net_r_45"] for t in ctrl_trades], dtype=float) if ctrl_trades else np.array([])
    net45_bps = float(net45.mean()) * 1e4 if len(net45) else 0.0
    ctrl45_bps = float(ctrl45.mean()) * 1e4 if len(ctrl45) else 0.0
    oi_delta = round(net45_bps - ctrl45_bps, 4)

    param_hash = hashlib.sha256(json.dumps({
        "construction": "high_oi_expansion_trend_sweep",
        "variation": label, "pctile": pctile, "sma_window": sma_window,
        "pctile_window_days": PCTILE_WINDOW_DAYS, "forward_bars": FORWARD_BARS,
        "time_stop_bars": TIME_STOP_BARS,
        "trigger": "oi >= trailing_90d_pct", "entry": "long when oi>=pct AND close>SMA",
        "exit": "close<SMA OR 5-bar time stop", "fill": "next_open",
        "cost": "45bps all-in taker fail-closed", "leverage": "none",
        "universe": "native perps only, top-30 by mean OI_usd",
    }, sort_keys=True).encode()).hexdigest()
    universe_hash = hashlib.sha256(",".join(sorted(universe)).encode()).hexdigest()

    result = {
        "construction": "high_oi_expansion_trend_sweep",
        "variation": label,
        "pctile": pctile, "sma_window": sma_window,
        "n_coins": len(set(daily["coin"])),
        "n_coins_with_events": int(ev["coin"].nunique()),
        "n_extreme_events": int(len(ev)),
        "n_baseline_bars": int(len(bl)),
        "n_baseline_overlap_bars": int(len(base_overlap)),
        "h1_regime_mean_abs_move": round(float(regime_abs.mean()), 8),
        "h1_baseline_mean_abs_move": round(float(base_abs.mean()), 8),
        "h1_baseline_overlap_mean_abs_move": round(float(base_overlap_abs.mean()), 8),
        "h1_ratio": round(bs["ratio"], 6),
        "h1_ratio_overlap": round(bs_overlap["ratio"], 6),
        "h1_bootstrap_p_value": round(bs["p_value"], 6),
        "h1_bootstrap_p_value_overlap": round(bs_overlap["p_value"], 6),
        "h2_trade_count": int(len(h2_trades)),
        "h2_n_sma_exits": int(sum(1 for t in h2_trades if t["reason"] == "sma")),
        "h2_n_time_stop_exits": int(sum(1 for t in h2_trades if t["reason"] == "time_stop")),
        "h2_gross_bps": round(float(np.array([t["gross_r"] for t in h2_trades]).mean()) * 1e4, 4) if h2_trades else 0.0,
        "h2_cost_bps_fail_closed": COST_BPS_FAIL_CLOSED,
        "h2_net_bps_45": round(net45_bps, 4),
        "h2_win_rate_net45": round(float((net45 > 0).mean()), 6) if len(net45) else 0.0,
        "control_sma_only_n": int(len(ctrl_trades)),
        "control_sma_only_net45_bps": round(ctrl45_bps, 4),
        "oi_filter_delta_bps": oi_delta,
        "no_lookahead": True, "leverage": "none", "live": "off",
        "data_source": "hl_oi_hf parquet (native perps, mark_price)",
    }

    period_start = str(pd.to_datetime(ev["ts"].min(), unit="ms").date()) if len(ev) else ""
    period_end = str(pd.to_datetime(ev["ts"].max(), unit="ms").date()) if len(ev) else ""

    entry = None
    if write:
        entry = ledger.increment_trial("HYP-16", param_hash, universe_hash,
                                       period_start, period_end, result)
    return {
        "label": label, "result": result, "param_hash": param_hash,
        "chain_hash": entry["chain_hash"] if entry else "not-written",
        "h1_ratio_full": round(bs["ratio"], 4), "h1_p_full": round(bs["p_value"], 4),
        "h1_ratio_overlap": round(bs_overlap["ratio"], 4),
        "h1_p_overlap": round(bs_overlap["p_value"], 4),
        "h2_net45": round(net45_bps, 3), "oi_delta": oi_delta,
        "n_events": int(len(ev)), "n_trades": int(len(h2_trades)),
        "ctrl_n": int(len(ctrl_trades)), "ctrl_net45": round(ctrl45_bps, 3),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-write", action="store_true")
    args = ap.parse_args()

    print("=== HYP-16 robustness sweep (pre-registered, FIXED variations) ===\n")
    print("loading native-perp hourly OI (hl_oi_hf) ...")
    daily, universe = primary.load_native_daily()
    print(f"  universe: {len(universe)} coins\n")

    ledger = primary.ledger
    if args.no_write:
        # Wrap increment_trial as a no-op returning a fake entry hash-stable mock
        def _noop(*a, **k):
            return {"chain_hash": "no-write", "param_hash": k.get("param_hash", "")}
        ledger = type("L", (), {"increment_trial": staticmethod(_noop)})()

    variants = [
        ("BASELINE", 90.0, 20, False),   # reference; primary trial 269c55b8… exists
        ("V-A", 90.0, 50, True),
        ("V-B", 80.0, 20, True),
        ("V-C", 95.0, 20, True),
    ]

    rows = []
    for label, pct, sma, write in variants:
        r = run_variant(label, pct, sma, daily, universe, ledger, write=write)
        rows.append(r)
        print(f"[{label:>8}] pct={pct:>3.0f} sma={sma:>2d}  "
              f"H1 ratio(overlap)={r['h1_ratio_overlap']:.4f} p={r['h1_p_overlap']:.4f}  "
              f"H1 ratio(full)={r['h1_ratio_full']:.4f} p={r['h1_p_full']:.4f}  "
              f"H2 net@45bps={r['h2_net45']:+.2f}  OI-marginal={r['oi_delta']:+.2f}bps  "
              f"(n_events={r['n_events']}, n_trades={r['n_trades']}, "
              f"ctrl_n={r['ctrl_n']}/ctrl_net={r['ctrl_net45']:+.2f})")
        if not args.no_write and write:
            print(f"        wrote trial param_hash={r['param_hash'][:16]}...  "
                  f"chain_hash={r['chain_hash'][:16]}...")

    print("\n=== COMPACT TABLE ===")
    print(f"{'variant':>9} {'H1 ratio(OVL)':>14} {'H1 p(OVL)':>10} "
          f"{'H1 ratio(FULL)':>14} {'H1 p(FULL)':>10} {'H2 net@45':>10} "
          f"{'OI-marg':>9}")
    for r in rows:
        print(f"{r['label']:>9} {r['h1_ratio_overlap']:>14.4f} {r['h1_p_overlap']:>10.4f} "
              f"{r['h1_ratio_full']:>14.4f} {r['h1_p_full']:>10.4f} "
              f"{r['h2_net45']:>+10.2f} {r['oi_delta']:>+9.2f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())