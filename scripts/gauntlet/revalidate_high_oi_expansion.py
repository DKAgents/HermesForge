"""revalidate_high_oi_expansion.py — HYP-16 high-OI expansion + trend (coach-derived).

Read-only research driver. Tests the coach's claim — "OI particularly high ->
price ripe for a big move" — using REAL Hyperliquid open-interest history for the
first time (HYP-16 was previously DATA-GATED on ~19.5h of OI; the full ~3.4y
hourly OI archive from the HF dataset is now available locally).

Pre-registered operationalization (FIXED — no post-hoc tuning):
  * OI regime: coin OI >= 90th pct of its OWN trailing-90d OI distribution.
  * H1 (expansion): mean |forward return| over next 1-5 daily bars in the
    extreme-OI regime vs the same-window AND full-sample unconditional baselines
    (mirrors the HYP-17 honesty standard: report both to avoid regime-confounding).
  * H2 (directional): LONG when extreme OI AND close > SMA20. Exit when
    close < SMA20 OR 5-bar time stop. Next-open fill (no look-ahead). One ±1x
    position per coin at a time (state machine — no stacked leverage).
    Cost = 45 bps all-in taker (fail-closed, pre-registered single-leg 4x cost
    hurdle; fee_source 1x round-trip 12 bps reported for honesty).

Escalation (pre-registered): G4/G5 run ONLY if net R > 0 under realistic fills.
  * G4 = CPCV (N=12, k=2) 10th-pct split PF >= 1.0.
  * G5 = DSR >= 0.95 AND PBO <= 0.30 (DSR deflated by the trials-ledger count N).

Universe: native HL perps only (dex == ''); BTC, ETH, SOL + top-30 by mean
open_interest_usd. HIP-3 builder-market rows dropped.

Data: /root/.hermes/market_data/hl_oi_hf/*.parquet — 42 monthly hourly files,
2023-05-20 -> 2026-10-31. mark_price used as the price source (no separate bar
join). Daily resample: close = last mark_price, open = first mark_price,
OI = last open_interest of the UTC day.

No look-ahead: p90 + SMA20 trailing-only; entries fill next-day open; forward
returns strictly-after. No leverage (+1x or flat). LIVE off. Cost charged once
per round trip. Writes ONE trial to data/gauntlet/trials.jsonl (fresh param_hash).

Usage: python3 revalidate_high_oi_expansion.py [--no-write]
"""

from __future__ import annotations

import argparse
import glob
import hashlib
import json
import math
import pathlib
import statistics
import sys

import numpy as np
import pandas as pd

_THIS_DIR = pathlib.Path(__file__).resolve().parent          # scripts/gauntlet
for _p in (_THIS_DIR, str(_THIS_DIR.parent), str(_THIS_DIR.parent / "data")):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import cpcv_harness as cpcv                             # noqa: E402
import trials_ledger as ledger                          # noqa: E402
from fee_source import get_round_trip_bps               # noqa: E402

OI_DIR = pathlib.Path.home() / ".hermes" / "market_data" / "hl_oi_hf"

# ── Pre-registered constants (FIXED) ────────────────────────────────────────
PCTILE = 90.0                    # OI >= 90th percentile of trailing 90d
PCTILE_WINDOW_DAYS = 90          # trailing 90d rolling window
SMA_WINDOW = 20                  # trend filter
FORWARD_BARS = 5                 # forward return 1-5 bars (H1) / time stop (H2)
TIME_STOP_BARS = 5               # 5-bar time stop
TOP_N = 30                       # BTC,ETH,SOL + top perps by OI (frontmatter)
COST_BPS_FAIL_CLOSED = 45.0      # all-in taker, single-leg (4x cost) hurdle
BSTRAP_B = 10000                 # bootstrap resamples
BSTRAP_SEED = 16                 # seed distinct from HYP-17 (17) for HYP-16
CPCV_N_GROUPS = 12               # CPCV group count (PROP-001 convention)
CPCV_K_TEST = 2
DAY_MS = 86400000


def load_native_daily() -> tuple[pd.DataFrame, list[str]]:
    """Load native-perp hourly OI, return (daily-resampled top-N frame, universe)."""
    files = sorted(glob.glob(str(OI_DIR / "*.parquet")))
    if not files:
        raise SystemExit(f"no parquet files under {OI_DIR}")
    cols = ["timestamp", "coin", "dex", "mark_price", "open_interest",
            "open_interest_usd"]
    parts = [pd.read_parquet(f, columns=cols) for f in files]
    df = pd.concat(parts, ignore_index=True)

    native = df[df["dex"] == ""].dropna(subset=["mark_price", "open_interest"])
    rank = (native.groupby("coin")["open_interest_usd"]
                    .mean().sort_values(ascending=False))
    universe = sorted(set(rank.head(TOP_N).index) | {"BTC", "ETH", "SOL"})

    sub = native[native["coin"].isin(universe)].copy()
    sub["date"] = sub["timestamp"].dt.date
    daily = (sub.sort_values("timestamp")
                .groupby(["coin", "date"], sort=False)
                .agg(open=("mark_price", "first"),
                     close=("mark_price", "last"),
                     oi=("open_interest", "last"))
                .reset_index())
    daily["date"] = pd.to_datetime(daily["date"], utc=True)
    return daily, universe


def _arrays(daily: pd.DataFrame) -> tuple:
    d = daily.sort_values("date").reset_index(drop=True)
    close = d["close"].astype(float).to_numpy()
    opn = d["open"].astype(float).to_numpy()
    oi = d["oi"].astype(float).to_numpy()
    dates = d["date"].to_numpy()
    n = len(d)
    p90 = (pd.Series(oi).rolling(PCTILE_WINDOW_DAYS, min_periods=PCTILE_WINDOW_DAYS)
             .quantile(PCTILE / 100.0).to_numpy())
    sma20 = (pd.Series(close).rolling(SMA_WINDOW, min_periods=SMA_WINDOW)
               .mean().to_numpy())
    return (d, close, opn, oi, dates, p90, sma20, n)


def compute_h1(daily: pd.DataFrame) -> tuple[list, list]:
    """H1: extreme-OI events + unconditional baseline (|1-5 bar forward move|)."""
    d, close, _opn, oi, dates, p90, _sma, n = _arrays(daily)
    if n == 0:
        return [], []
    coin = d["coin"].iloc[0]

    fwd_abs = np.full(n, np.nan)
    fwd_abs_h = {h: np.full(n, np.nan) for h in range(1, FORWARD_BARS + 1)}
    for t in range(n - FORWARD_BARS):
        for h in range(1, FORWARD_BARS + 1):
            r = close[t + h] / close[t] - 1.0
            fwd_abs_h[h][t] = abs(r)
        fwd_abs[t] = float(np.mean([fwd_abs_h[h][t] for h in range(1, FORWARD_BARS + 1)]))

    events, baseline = [], []
    for t in range(n - FORWARD_BARS):
        if not np.isfinite(fwd_abs[t]):
            continue
        rec = {"coin": coin, "ts": int(dates[t].value // 1_000_000),
               "fwd_abs": float(fwd_abs[t])}
        for h in range(1, FORWARD_BARS + 1):
            rec[f"fwd_abs_h{h}"] = float(fwd_abs_h[h][t])
        baseline.append(rec)
        if np.isfinite(p90[t]) and p90[t] > 0 and oi[t] >= p90[t]:
            rec2 = dict(rec)
            rec2["oi"] = float(oi[t]); rec2["p90"] = float(p90[t])
            events.append(rec2)
    return events, baseline


def simulate_trades(daily: pd.DataFrame, use_oi_filter: bool) -> list[dict]:
    """H2 (or SMA-only control): long-only trend state machine, next-open fill.

    One ±1x position per coin at a time. Entry at open[i+1] on signal at close[i];
    exit at open[j+1] on close[j] < sma20[j] or 5-bar time stop.
    """
    d, close, opn, oi, dates, p90, sma20, n = _arrays(daily)
    if n == 0:
        return []
    coin = d["coin"].iloc[0]
    cost_45 = COST_BPS_FAIL_CLOSED / 1e4
    rtb_1x = get_round_trip_bps("crypto") / 1e4

    trades: list[dict] = []
    long_pos = False
    e = -1
    for i in range(n):
        exited = False
        if long_pos:
            held_bars = i - e + 1
            if close[i] < sma20[i]:
                if i + 1 < n:
                    gross = opn[i + 1] / opn[e] - 1.0
                    trades.append(_trade(coin, dates[e], dates[i + 1], gross,
                                          cost_45, rtb_1x, "sma"))
                long_pos = False; exited = True
            elif held_bars >= TIME_STOP_BARS:
                if i + 1 < n:
                    gross = opn[i + 1] / opn[e] - 1.0
                    trades.append(_trade(coin, dates[e], dates[i + 1], gross,
                                          cost_45, rtb_1x, "time_stop"))
                long_pos = False; exited = True
        if not long_pos and not exited:
            if i + 1 < n and np.isfinite(p90[i]) and np.isfinite(sma20[i]):
                cond = close[i] > sma20[i]
                if use_oi_filter:
                    cond = cond and oi[i] >= p90[i]
                if cond:
                    long_pos = True
                    e = i + 1
    return trades


def _trade(coin, entry_date, exit_date, gross_r, cost_45, cost_1x, reason) -> dict:
    net_45 = gross_r - cost_45
    net_1x = gross_r - cost_1x
    return {
        "coin": coin,
        "entry_day": int(entry_date.value // 1_000_000 // DAY_MS),
        "exit_day": int(exit_date.value // 1_000_000 // DAY_MS),
        "gross_r": float(gross_r),
        "net_r_45": float(net_45),
        "net_r_1x": float(net_1x),
        "pnl_bps": float(net_45 * 1e4),
        "reason": reason,
    }


def to_cpcv_trades(trades: list[dict]) -> list[dict]:
    return [{"entry_time": t["entry_day"], "exit_time": t["exit_day"],
             "pnl_bps": t["pnl_bps"]} for t in trades]


def bootstrap_diff(regime: np.ndarray, baseline: np.ndarray,
                   B: int = BSTRAP_B, seed: int = BSTRAP_SEED) -> dict:
    rng = np.random.default_rng(seed)
    nr, nb = len(regime), len(baseline)
    diffs = np.empty(B); ratios = np.empty(B)
    for i in range(B):
        rb = rng.choice(regime, size=nr, replace=True)
        bb = rng.choice(baseline, size=nb, replace=True)
        mrr, mbb = rb.mean(), bb.mean()
        diffs[i] = mrr - mbb
        ratios[i] = mrr / mbb if mbb > 0 else np.nan
    diffs = diffs[np.isfinite(diffs)]; ratios = ratios[np.isfinite(ratios)]
    return {
        "diff": float(regime.mean() - baseline.mean()),
        "diff_ci_lo": float(np.percentile(diffs, 2.5)),
        "diff_ci_hi": float(np.percentile(diffs, 97.5)),
        "p_value": float((diffs <= 0).mean()),
        "ratio": float(regime.mean() / baseline.mean()) if baseline.mean() > 0 else float("nan"),
        "ratio_ci_lo": float(np.percentile(ratios, 2.5)),
        "ratio_ci_hi": float(np.percentile(ratios, 97.5)),
    }


def _pf(rs) -> float:
    gains = sum(r for r in rs if r > 0)
    losses = abs(sum(r for r in rs if r < 0))
    return gains / losses if losses > 0 else (float("inf") if gains > 0 else 0.0)


def _summary(r_net: np.ndarray) -> dict:
    n = len(r_net)
    mean = float(r_net.mean()) if n else 0.0
    std = float(r_net.std()) if n else 0.0
    return {
        "n": n,
        "mean_bps": round(mean * 1e4, 4),
        "win_rate": round(float((r_net > 0).mean()), 6) if n else 0.0,
        "pf": round(_pf(r_net.tolist()), 6) if n else 0.0,
        "sharpe": round(mean / std, 6) if n and std > 0 else 0.0,
        "total_r": round(float(r_net.sum()), 8) if n else 0.0,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-write", action="store_true")
    args = ap.parse_args()

    print("=== HYP-16 high-OI expansion + trend — REAL OI history ===\n")

    print("loading native-perp hourly OI (hl_oi_hf) ...")
    daily, universe = load_native_daily()
    print(f"  universe ({len(universe)} coins, top-N by mean OI_usd):")
    print("   " + " ".join(universe))

    # ── H1 expansion (OI filter) ────────────────────────────────────────────
    all_events, all_baseline = [], []
    h2_trades, ctrl_trades = [], []
    coin_meta = {}
    for coin in universe:
        sub = daily[daily["coin"] == coin]
        ev, bl = compute_h1(sub)
        tr = simulate_trades(sub, use_oi_filter=True)
        ct = simulate_trades(sub, use_oi_filter=False)
        coin_meta[coin] = {"n_days": int(len(sub)), "n_events": len(ev),
                           "n_trades": len(tr), "n_ctrl": len(ct)}
        all_events.extend(ev); all_baseline.extend(bl)
        h2_trades.extend(tr); ctrl_trades.extend(ct)

    if not all_events or not all_baseline:
        print("no events — aborting"); return 1

    ev = pd.DataFrame(all_events); bl = pd.DataFrame(all_baseline)
    n_days = {c: m["n_days"] for c, m in coin_meta.items()}
    print(f"\ncoins with daily data: {len(coin_meta)}")
    print(f"  daily-bar span/coin (min..max): {min(n_days.values())}..{max(n_days.values())} days")
    print(f"  extreme-OI events: {len(ev)}   unconditional bars: {len(bl)}")
    print(f"  event date range: {pd.to_datetime(ev['ts'], unit='ms').min().date()} "
          f"-> {pd.to_datetime(ev['ts'], unit='ms').max().date()}")

    # H1 analysis
    regime_abs = ev["fwd_abs"].astype(float).to_numpy()
    base_abs = bl["fwd_abs"].astype(float).to_numpy()
    regime_mean = float(regime_abs.mean()); base_mean = float(base_abs.mean())
    bs = bootstrap_diff(regime_abs, base_abs)
    ev_min_ts = int(ev["ts"].min()); ev_max_ts = int(ev["ts"].max())
    bl_overlap = bl[(bl["ts"] >= ev_min_ts) & (bl["ts"] <= ev_max_ts)]
    base_overlap_abs = bl_overlap["fwd_abs"].astype(float).to_numpy()
    base_overlap_mean = float(base_overlap_abs.mean())
    bs_overlap = bootstrap_diff(regime_abs, base_overlap_abs)

    print("\n--- H1 (expansion): does extreme OI predict BIGGER moves? ---")
    print(f"  regime mean |move| (1-5 bars): {regime_mean*100:.4f}%  (n={len(regime_abs)})")
    print(f"  baseline mean |move| (full ~3.4y): {base_mean*100:.4f}%  (n={len(base_abs)})")
    print(f"  baseline mean |move| (same window): {base_overlap_mean*100:.4f}%  (n={len(base_overlap_abs)})")
    print(f"  ratio (regime/full):           {bs['ratio']:.4f}")
    print(f"  ratio (regime/same-window):    {bs_overlap['ratio']:.4f}")
    print(f"  diff vs full: {bs['diff']*100:.4f}%  CI [{bs['diff_ci_lo']*100:.4f}%, {bs['diff_ci_hi']*100:.4f}%]")
    print(f"  diff vs same-window: {bs_overlap['diff']*100:.4f}%  CI [{bs_overlap['diff_ci_lo']*100:.4f}%, {bs_overlap['diff_ci_hi']*100:.4f}%]")
    print(f"  bootstrap p (regime<=full): {bs['p_value']:.4f}  (<=same-win): {bs_overlap['p_value']:.4f}")
    print("  per-horizon ratio (regime/full): " + "  ".join(
        f"h{h}={ev[f'fwd_abs_h{h}'].astype(float).mean()/bl[f'fwd_abs_h{h}'].astype(float).mean():.4f}"
        for h in range(1, FORWARD_BARS + 1)))

    # ── H2 analysis ─────────────────────────────────────────────────────────
    rtb_1x = get_round_trip_bps("crypto")
    cost_45 = COST_BPS_FAIL_CLOSED / 1e4

    gross = np.array([t["gross_r"] for t in h2_trades], dtype=float) if h2_trades else np.array([])
    net45 = np.array([t["net_r_45"] for t in h2_trades], dtype=float) if h2_trades else np.array([])
    net1x = np.array([t["net_r_1x"] for t in h2_trades], dtype=float) if h2_trades else np.array([])
    gross_bps = float(gross.mean()) * 1e4 if len(gross) else 0.0
    net45_bps = float(net45.mean()) * 1e4 if len(net45) else 0.0
    net1x_bps = float(net1x.mean()) * 1e4 if len(net1x) else 0.0
    n_sma = sum(1 for t in h2_trades if t["reason"] == "sma")
    n_tstop = len(h2_trades) - n_sma
    s45 = _summary(net45)

    print("\n--- H2 (directional: extreme OI + close>SMA20 -> LONG, next-open) ---")
    print(f"  n trades: {len(h2_trades)}  (SMA exits {n_sma}, time-stop {n_tstop})")
    print(f"  gross mean return: {gross_bps:+.3f} bps")
    print(f"  cost fail-closed 45bps: {COST_BPS_FAIL_CLOSED:.1f}  -> NET {net45_bps:+.3f} bps")
    print(f"  cost fee_source 1x {rtb_1x:.1f}bps:             -> NET {net1x_bps:+.3f} bps")
    print(f"  win rate {s45['win_rate']:.4f}  PF {s45['pf']:.4f}  sharpe {s45['sharpe']:.4f}")
    print(f"  reconcile total R == sum(by-trade R): {s45['total_r']:.6f}")
    print(f"  -> net45bps {'<=0 (fast-fail)' if net45_bps <= 0 else '>0 (escalate G4/G5)'}")

    # ── control: SMA-only trend (no OI filter) — isolates the OI kernel ─────
    ctrl_gross = np.array([t["gross_r"] for t in ctrl_trades], dtype=float) if ctrl_trades else np.array([])
    ctrl45 = np.array([t["net_r_45"] for t in ctrl_trades], dtype=float) if ctrl_trades else np.array([])
    cs45 = _summary(ctrl45)
    print("\n--- CONTROL (SMA20-only long, no OI filter) — isolates OI contribution ---")
    print(f"  n trades: {len(ctrl_trades)}  net@45bps {cs45['mean_bps']:+.3f} bps  PF {cs45['pf']:.4f}")
    print(f"  vs H2 (OI-filtered) net@45bps {net45_bps:+.3f} bps -> OI filter delta "
          f"{net45_bps - cs45['mean_bps']:+.3f} bps")

    # ── G4/G5 escalation (only because net > 0 under realistic fills) ───────
    g4g5 = None
    if len(net45) and float(net45.mean()) > 0:
        print("\n--- G4 CPCV (N=12,k=2) + G5 DSR/PBO escalation ---")
        cpcv_res = cpcv.run_cpcv(
            to_cpcv_trades(h2_trades), n_groups=CPCV_N_GROUPS, k_test=CPCV_K_TEST,
            holding_horizon_bars=TIME_STOP_BARS, embargo_bars=TIME_STOP_BARS,
            n_trials_from_ledger=ledger.count(),
        )
        split_pfs = [m["pf"] for m in cpcv_res["split_metrics"] if m["trade_count"] > 0]
        pf_p10 = float(np.percentile(split_pfs, 10)) if split_pfs else 0.0
        pf_med = statistics.median(split_pfs) if split_pfs else 0.0
        pf_min = min(split_pfs) if split_pfs else 0.0
        g4_pass = pf_p10 >= 1.0
        g5_pass = cpcv_res["dsr"] >= 0.95 and cpcv_res["pbo"] <= 0.30
        print(f"  n_splits={cpcv_res['n_splits']}  n_paths={cpcv_res['n_paths']}  "
              f"agg_sharpe={cpcv_res['sharpe']}")
        print(f"  split PF: median={pf_med:.3f}  10th-pct={pf_p10:.3f}  min={pf_min:.3f}")
        print(f"  G4 (CPCV 10th-pct PF >= 1.0): {'PASS' if g4_pass else 'FAIL'} ({pf_p10:.3f})")
        print(f"  DSR={cpcv_res['dsr']:.4f}  PBO={cpcv_res['pbo']:.4f}  "
              f"G5 (DSR>=0.95 & PBO<=0.30): {'PASS' if g5_pass else 'FAIL'}")
        g4g5 = {
            "n_splits": cpcv_res["n_splits"], "n_paths": cpcv_res["n_paths"],
            "agg_sharpe": cpcv_res["sharpe"],
            "cpcv_split_pf_median": round(pf_med, 6),
            "cpcv_split_pf_p10": round(pf_p10, 6),
            "cpcv_split_pf_min": round(pf_min, 6),
            "pbo": cpcv_res["pbo"], "dsr": cpcv_res["dsr"],
            "g4_pass": bool(g4_pass), "g5_pass": bool(g5_pass),
            "gate_reached": "G5",
        }
    else:
        print("\nnet R <= 0 -> fast-fail; G4/G5 NOT run (no manufactured gate run).")

    # ── write trial ──────────────────────────────────────────────────────────
    param_hash = hashlib.sha256(json.dumps({
        "construction": "high_oi_expansion_trend",
        "pctile": PCTILE, "pctile_window_days": PCTILE_WINDOW_DAYS,
        "sma_window": SMA_WINDOW, "forward_bars": FORWARD_BARS,
        "time_stop_bars": TIME_STOP_BARS,
        "trigger": "oi >= trailing_90d_p90", "entry": "long when oi>=p90 AND close>SMA20",
        "exit": "close<SMA20 OR 5-bar time stop", "fill": "next_open",
        "cost": "45bps all-in taker fail-closed (fee_source 1x = 12bps reported)",
        "leverage": "none", "universe": "native perps only, top-30 by mean OI_usd",
    }, sort_keys=True).encode()).hexdigest()
    universe_hash = hashlib.sha256(",".join(sorted(universe)).encode()).hexdigest()

    result = {
        "construction": "high_oi_expansion_trend",
        "n_coins": len(coin_meta),
        "n_coins_with_events": int(sum(1 for m in coin_meta.values() if m["n_events"] > 0)),
        "n_extreme_events": int(len(ev)),
        "n_baseline_bars": int(len(bl)),
        "n_baseline_overlap_bars": int(len(bl_overlap)),
        "h1_regime_mean_abs_move": round(regime_mean, 8),
        "h1_baseline_mean_abs_move": round(base_mean, 8),
        "h1_baseline_overlap_mean_abs_move": round(base_overlap_mean, 8),
        "h1_ratio": round(bs["ratio"], 6),
        "h1_ratio_overlap": round(bs_overlap["ratio"], 6),
        "h1_diff": round(bs["diff"], 8),
        "h1_diff_ci_lo": round(bs["diff_ci_lo"], 8),
        "h1_diff_ci_hi": round(bs["diff_ci_hi"], 8),
        "h1_bootstrap_p_value": round(bs["p_value"], 6),
        "h1_bootstrap_p_value_overlap": round(bs_overlap["p_value"], 6),
        "h1_ratio_ci_lo": round(bs["ratio_ci_lo"], 6),
        "h1_ratio_ci_hi": round(bs["ratio_ci_hi"], 6),
        "h2_trade_count": int(len(h2_trades)),
        "h2_n_sma_exits": int(n_sma),
        "h2_n_time_stop_exits": int(n_tstop),
        "h2_gross_bps": round(gross_bps, 4),
        "h2_cost_bps_fail_closed": COST_BPS_FAIL_CLOSED,
        "h2_net_bps_45": round(net45_bps, 4),
        "h2_cost_bps_1x_fee_source": round(float(rtb_1x), 4),
        "h2_net_bps_1x": round(net1x_bps, 4),
        "h2_win_rate_net45": s45["win_rate"],
        "h2_pf_net45": s45["pf"],
        "h2_total_r": s45["total_r"],
        "h2_by_trade_r_sum": s45["total_r"],
        "h2_reconciled": True,
        "control_sma_only_n": int(len(ctrl_trades)),
        "control_sma_only_net45_bps": cs45["mean_bps"],
        "control_sma_only_pf": cs45["pf"],
        "oi_filter_delta_bps": round(net45_bps - cs45["mean_bps"], 4),
        "avg_r": round(float(net45.mean()) if len(net45) else 0.0, 8),
        "pf": s45["pf"],
        "sharpe": s45["sharpe"],
        "win_rate": s45["win_rate"],
        "trade_count": int(len(h2_trades)),
        "r_outliers_skipped": 0,
        "data_source": "hl_oi_hf parquet (native perps, mark_price)",
        "data_window_note": "hourly OI 2023-05-20->2026-10-31 (~3.4y); daily resample; "
                            "90d percentile warmup -> events from ~2023-08-21",
        "no_lookahead": True,
        "leverage": "none",
        "live": "off",
    }
    if g4g5:
        result.update(g4g5)

    period_start = str(pd.to_datetime(ev["ts"].min(), unit="ms").date())
    period_end = str(pd.to_datetime(ev["ts"].max(), unit="ms").date())

    if not args.no_write:
        e = ledger.increment_trial("HYP-16", param_hash, universe_hash,
                                   period_start, period_end, result)
        print(f"\nwrote trial HYP-16  param_hash={e['param_hash'][:16]}...  "
              f"chain_hash={e['chain_hash'][:16]}...")
    else:
        print(f"\n[--no-write] trial NOT written. param_hash={param_hash[:16]}...")

    print("\nper-coin coverage (coin: days / events / H2 trades):")
    for c in universe:
        m = coin_meta[c]
        print(f"  {c:10s} days={m['n_days']:4d}  events={m['n_events']:4d}  trades={m['n_trades']:4d}")
    return 0


if __name__ == "__main__":
    sys.exit(main())