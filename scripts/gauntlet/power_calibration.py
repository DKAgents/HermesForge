#!/usr/bin/env python3
"""power_calibration.py — US-06 M-4: strategy-gauntlet POWER CALIBRATION harness.

Addresses the critical review's core critique: "statistical power was never
measured." A null result only means "no edge" if the gauntlet *could* have
detected a real edge of meaningful size at this account's sample length,
turnover, and trial count. This harness measures that detection power directly.

WHAT IT DOES
  Inject SYNTHETIC edges of KNOWN strength (per-trade Sharpe 0.5/1.0/1.5, and
  information coefficient IC 0.01/0.02/0.04) into REAL Hyperliquid 6h price
  data, charge realistic taker round-trip cost (fee_source), then run each
  synthetic trade set through the EXISTING gate evaluators (G0 cost screen,
  G1 power, G3 fill-realism, G4 CPCV, G5 DSR/PBO, G6 regime) and record the
  PASS RATES across a Monte Carlo of edge realizations.

  If a Sharpe-1.0 edge FAILS most of the time, the thresholds are miscalibrated
  for this account size and the harness says so explicitly (with a revision
  recommendation) — it NEVER changes the thresholds itself.

GATE COVERAGE (honest)
  * G0 cost screen  — computed ONCE on real data (deterministic; the market's
                       median |move| vs 4x all-in cost does not depend on the
                       injected edge). Reported as a pre-condition, not per-seed.
  * G1 power        — evaluate_g1 on the net edge's measured mu_R/sigma_R.
  * G2 leakage       — N/A by construction: an injected i.i.d. edge has no
                       look-ahead / funding / OI lag. Reported, not faked.
  * G3 fill-realism  — evaluate_fill_realism (bar-level model; cost_adjuster).
  * G4 CPCV          — run_cpcv 10th-pct split PF >= 1.0.
  * G5 DSR/PBO       — compute_dsr >= 0.95 (deflated by the trials-ledger N),
                       PBO <= 0.30.
  * G6 regime        — evaluate_g6 on real price regime structure (the injected
                       edge is regime-independent by construction).

RE-RUN cadence: annually, or after ANY gate threshold change (US-06 M-4).

Usage:
    python3 power_calibration.py            # full table (200 seeds/edge)
    python3 power_calibration.py --quick    # 30 seeds/edge (fast smoke test)
    python3 power_calibration.py --json     # machine-readable
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys

import numpy as np
import pandas as pd

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
if _THIS_DIR not in sys.path:
    sys.path.insert(0, _THIS_DIR)

import cpcv_harness as cv            # noqa: E402
import g0_cost_screen               # noqa: E402
import g1_gate                      # noqa: E402
import g3_gate                      # noqa: E402
import g6_regime_robustness as g6   # noqa: E402
import mde                          # noqa: E402
import trials_ledger as ledger      # noqa: E402
from fee_source import get_round_trip_bps  # noqa: E402


# ── Harness configuration (account-size anchored) ────────────────────────────
DATA_DIR = os.path.expanduser("~/.hermes/market_data")
PARQUET_6H = os.path.join(DATA_DIR, "6h")
BASE_TICKER = "BTC"

ASSET_CLASS = "crypto"
TIMEFRAME = "1d"          # route G3 to the bar-level model (no L2 snapshots)
RISK_FRAC = 0.01          # 1% stop distance -> cost drag in R units
SIGMA_R = 1.0             # per-trade R volatility (unit-scale R multiples)
HOLDING_BARS = 6          # 6h bars held (~36h swing) -> CPCV purge/embargo unit

G4_PF_PCT = 10.0          # G4: 10th-pct split PF >= G4_PF_FLOOR
G4_PF_FLOOR = 1.0
G5_DSR_THRESHOLD = 0.95   # G5: DSR >= threshold (matches g4g5_hyp25)
G5_PBO_MAX = 0.30         # G5: PBO <= max
G6_REGIME_SCORE = 0.75    # G6: regime_score >= threshold (matches g6 module)

# Edge strengths to inject: (label, kind, strength). kind in {"sharpe","ic"}.
EDGE_STRENGTHS = [
    ("Sharpe 0.0 (null ctrl)", "sharpe", 0.0),
    ("Sharpe 0.5", "sharpe", 0.5),
    ("Sharpe 1.0", "sharpe", 1.0),
    ("Sharpe 1.5", "sharpe", 1.5),
    ("IC 0.01", "ic", 0.01),
    ("IC 0.02", "ic", 0.02),
    ("IC 0.04", "ic", 0.04),
]


# ── Real data loading ────────────────────────────────────────────────────────

def load_real_prices(ticker: str = BASE_TICKER) -> np.ndarray:
    """Return the real Hyperliquid 6h close series for ``ticker`` (ascending)."""
    path = os.path.join(PARQUET_6H, f"{ticker}.parquet")
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"6h parquet not found: {path} (expects ~/.hermes/market_data/6h/)")
    df = pd.read_parquet(path)
    closes = df["close"].dropna().to_numpy(dtype=float)
    closes = closes[closes > 0]
    if len(closes) < 40:
        raise ValueError(f"{ticker}: only {len(closes)} valid closes — too few")
    return closes


# ── G0 pre-condition (once, on real data) ────────────────────────────────────

def run_g0(close_prices: np.ndarray) -> dict:
    """G0 cost pre-screen on the real price series (deterministic)."""
    return g0_cost_screen.screen(
        BASE_TICKER, close_prices,
        execution_mode="taker", maker_demonstrated=False)


# ── Edge injection ───────────────────────────────────────────────────────────

def inject_sharpe_edge(rng: np.random.Generator, n: int,
                       sharpe: float, sigma: float) -> np.ndarray:
    """n gross per-trade R ~ N(sharpe*sigma, sigma)."""
    return rng.normal(sharpe * sigma, sigma, n)


def inject_ic_edge(rng: np.random.Generator, n: int,
                   ic: float, sigma: float) -> np.ndarray:
    """Gross per-trade R for a strategy trading sign(signal), corr(signal,ret)=ic.

    signal s ~ N(0,1); return r = ic*s + sqrt(1-ic^2)*eps, eps ~ N(0,1) so that
    corr(s, r) = ic and r ~ N(0, sigma). Position = sign(s) => gross R = sign(s)*r
    with E[gross R] = ic * sigma * sqrt(2/pi).
    """
    s = rng.normal(0.0, 1.0, n)
    eps = rng.normal(0.0, 1.0, n)
    r = ic * s + math.sqrt(max(0.0, 1.0 - ic * ic)) * eps
    r = r * sigma
    return np.sign(s) * r


def cost_drag_r() -> float:
    """Realistic all-in round-trip cost in R units (fee_source -> R at RISK_FRAC)."""
    bps = get_round_trip_bps(ASSET_CLASS)          # 2*taker + slip + funding
    return (bps / 10000.0) / RISK_FRAC             # cost_R = bps / risk_frac


# ── Trade construction ───────────────────────────────────────────────────────

def build_trades(gross_r: np.ndarray, entry_prices: np.ndarray,
                 drag: float) -> list[dict]:
    """Attach injected gross edge to real entry prices; net_r = gross - drag.

    Trades are NON-OVERLAPPING in CPCV time: entry_time = i * HOLDING_BARS,
    exit_time = (i+1) * HOLDING_BARS. ``entry_prices`` is a chronological,
    multi-regime-spanned sample of the real close series (so G6 regime
    classification sees real bull/bear/flat structure, not a single-regime
    slice of one quarter).
    """
    n = len(gross_r)
    trades = []
    for i in range(n):
        entry = float(entry_prices[i])
        stop = entry * (1.0 - RISK_FRAC)
        gr = float(gross_r[i])
        trades.append({
            "entry_time": int(i * HOLDING_BARS),
            "exit_time": int((i + 1) * HOLDING_BARS),
            "entry_price": entry,
            "stop_price": stop,
            "direction": "long",
            "asset_class": ASSET_CLASS,
            "r_multiple": gr,          # gross (G3 re-derives cost drag)
            "gauntlet_r": gr - drag,   # net (used by G4/G5/G6)
            "pnl_bps": gr - drag,      # net R as CPCV P&L
        })
    return trades


def _regime_price_sample(closes: np.ndarray, n_trades: int) -> np.ndarray:
    """Evenly drop the real close series down to n_trades points so the trade
    set spans the FULL sample period (multiple market regimes), not a single
    contiguous quarter that may sit in one regime (which would make G6's
    regime-count floor unreachable as a data artifact rather than an edge fact)."""
    idx = np.linspace(0, len(closes) - 1, n_trades).round().astype(int)
    return closes[idx]


# ── Gate evaluation ───────────────────────────────────────────────────────────

def run_gates(trades: list[dict], net_r: np.ndarray,
              n_trials: int) -> dict:
    """Run G1/G3/G4/G5/G6 on one synthetic trade set; return per-gate record."""
    n = len(trades)
    out = {}

    # G1 — statistical power floor (measured mu_R/sigma_R of the NET edge).
    mu = float(net_r.mean())
    sigma = float(net_r.std(ddof=1)) if n > 1 else 1e-15
    g1 = g1_gate.evaluate_g1(
        signal_count=n, distinct_symbols=15,
        mu_r=mu, sigma_r=sigma,
        max_order_usd=10_000.0, top5_depth_usd_10bps=5_000_000.0)
    out["G1"] = {"passed": g1["passed"], "reasons": g1["reasons"],
                 "n_min_power": g1["n_min_power"], "mu_r": round(mu, 4),
                 "sigma_r": round(sigma, 4)}

    # G3 — fill realism (bar-level model re-derives cost drag from prices).
    g3 = g3_gate.evaluate_fill_realism("power_calibration", trades,
                                       ASSET_CLASS, TIMEFRAME)
    out["G3"] = {"passed": g3["passed"], "reasons": g3["reasons"],
                 "realistic_mean_r": g3["realistic_mean_r"],
                 "pessimistic_pf": g3["pessimistic_pf"]}

    # G4/G5 — CPCV + DSR/PBO (honest non-overlapping n == len(trades)).
    res = cv.run_cpcv(trades, n_groups=12, k_test=2,
                      n_trials_from_ledger=n_trials,
                      holding_horizon_bars=HOLDING_BARS,
                      embargo_bars=2 * HOLDING_BARS)
    pfs = sorted(m["pf"] for m in res["split_metrics"])
    nn = len(pfs)
    p10 = pfs[int(math.ceil(G4_PF_PCT / 100.0 * nn)) - 1] if nn else 0.0
    g4_pass = nn > 0 and p10 >= G4_PF_FLOOR
    out["G4"] = {"passed": g4_pass, "pf_10th_pct": round(p10, 4),
                 "n_splits": res["n_splits"]}

    sharpe = float(net_r.mean()) / float(net_r.std(ddof=1)) if n > 1 else 0.0
    skew = float(pd.Series(net_r).skew()) if n > 2 else 0.0
    kurt = float(pd.Series(net_r).kurt()) if n > 3 else 0.0
    dsr = cv.compute_dsr(sharpe, skew, kurt, n_trials, n)
    dsr_pass = dsr >= G5_DSR_THRESHOLD
    pbo_pass = res["pbo"] <= G5_PBO_MAX
    # G5 is the conjunction DSR AND PBO; report the two sub-gates separately so
    # the BINDING failure is visible (PBO vs DSR), not hidden behind one boolean.
    out["G5_dsr"] = {"passed": dsr_pass, "dsr": round(dsr, 4), "sharpe": round(sharpe, 4)}
    out["G5_pbo"] = {"passed": pbo_pass, "pbo": res["pbo"]}

    # G6 — regime robustness (real price structure, i.i.d. edge by construction).
    g6_res = g6.evaluate_g6(trades, asset_class=ASSET_CLASS,
                            apply_cost_adjustment=False)
    out["G6"] = {"passed": g6_res["passes"],
                 "regime_score": g6_res["regime_score"],
                 "regime_count": g6_res["regime_count"]}

    out["passed_all"] = all(out[g]["passed"]
                            for g in ("G1", "G3", "G4", "G5_dsr", "G5_pbo", "G6"))
    return out


# ── Monte Carlo ──────────────────────────────────────────────────────────────

def calibrate(n_trades: int, n_seeds: int,
              entry_prices: np.ndarray) -> dict:
    """Run the Monte Carlo; return per-edge pass-rate table + config."""
    n_trials = ledger.count()
    drag = cost_drag_r()

    # entry prices: a multi-regime sample of the REAL close series (see
    # _regime_price_sample). deterministic — edge injection is the only
    # per-seed stochastic component.
    win = _regime_price_sample(entry_prices, n_trades)

    g0 = run_g0(entry_prices)

    table = []
    GATES = ("G1", "G3", "G4", "G5_dsr", "G5_pbo", "G6")
    for label, kind, strength in EDGE_STRENGTHS:
        gate_hits = {g: 0 for g in GATES}
        all_hits = 0
        pbo_sum = 0.0
        dsr_sum = 0.0
        for seed in range(n_seeds):
            rng = np.random.default_rng(seed)
            if kind == "sharpe":
                gross = inject_sharpe_edge(rng, n_trades, strength, SIGMA_R)
            else:
                gross = inject_ic_edge(rng, n_trades, strength, SIGMA_R)
            trades = build_trades(gross, win, drag)
            net_r = np.array([t["gauntlet_r"] for t in trades])
            res = run_gates(trades, net_r, n_trials)
            for g in GATES:
                if res[g]["passed"]:
                    gate_hits[g] += 1
            pbo_sum += res["G5_pbo"]["pbo"]
            dsr_sum += res["G5_dsr"]["dsr"]
            if res["passed_all"]:
                all_hits += 1
        row = {
            "edge": label, "kind": kind, "strength": strength,
            "n_seeds": n_seeds,
            "net_mean_r": round((strength * SIGMA_R if kind == "sharpe"
                                 else strength * SIGMA_R * math.sqrt(2.0 / math.pi))
                                - drag, 4),
            "pass_rate_all": round(all_hits / n_seeds, 4),
            "gate_pass_rates": {g: round(gate_hits[g] / n_seeds, 4)
                                for g in GATES},
            "mean_pbo": round(pbo_sum / n_seeds, 4),
            "mean_dsr": round(dsr_sum / n_seeds, 4),
        }
        table.append(row)

    return {
        "config": {
            "n_trades": n_trades, "n_seeds": n_seeds, "n_trials_ledger": n_trials,
            "sigma_r": SIGMA_R, "risk_frac": RISK_FRAC,
            "cost_drag_r": round(drag, 4),
            "round_trip_bps": get_round_trip_bps(ASSET_CLASS),
            "asset_class": ASSET_CLASS, "timeframe": TIMEFRAME,
            "ticker": BASE_TICKER, "n_bars": len(entry_prices),
            "gate_thresholds": {
                "G4_pf_10th_pct_floor": G4_PF_FLOOR,
                "G5_dsr": G5_DSR_THRESHOLD, "G5_pbo": G5_PBO_MAX,
                "G6_regime_score": G6_REGIME_SCORE,
            },
        },
        "g0": g0,
        "mde": {
            "sharpe_dsr": round(mde.mde_sharpe_dsr(n_trades, n_trials), 4),
            "sharpe_single": round(mde.mde_sharpe(n_trades, n_trials), 4),
            "ic_breadth1": round(mde.mde_ic(n_trades, n_trials, 1.0), 4),
            "ic_breadth30": round(mde.mde_ic(n_trades, n_trials, 30.0), 4),
        },
        "table": table,
    }


# ── Reporting ────────────────────────────────────────────────────────────────

def _fmt_text(c: dict) -> str:
    cfg = c["config"]
    lines = []
    lines.append("=== Strategy Gauntlet POWER CALIBRATION (US-06 M-4) ===")
    lines.append(f"real data: {cfg['ticker']} 6h closes ({cfg['n_bars']} bars) · "
                 f"{cfg['n_trades']} trades/run · {cfg['n_seeds']} seeds/edge")
    lines.append(f"cost: round-trip {cfg['round_trip_bps']:.1f} bps -> "
                 f"{cfg['cost_drag_r']:.3f} R @ {cfg['risk_frac']:.0%} stop · "
                 f"sigma_R={cfg['sigma_r']} · trials-ledger N={cfg['n_trials_ledger']}")
    lines.append(f"G0 (real data): median move {c['g0']['median_abs_move_bps']:.1f} bps vs "
                 f"needed {c['g0']['gross_capture_needed_bps']:.1f} bps -> "
                 f"{'PASS' if c['g0']['passes'] else 'FAIL'}")
    lines.append("")
    lines.append("MDE at this sample/trial count (detection floor):")
    lines.append(f"  Sharpe (DSR-deflated) = {c['mde']['sharpe_dsr']:.3f}   "
                 f"(single-hypothesis {c['mde']['sharpe_single']:.3f})")
    lines.append(f"  IC breadth=1 = {c['mde']['ic_breadth1']:.3f}   "
                 f"breadth=30 = {c['mde']['ic_breadth30']:.3f}")
    lines.append("")
    hdr = (f"{'injected edge':22s} {'net R/trade':>11s} {'ALL':>6s} "
           f"{'G1':>6s} {'G3':>6s} {'G4':>6s} {'DSR':>6s} {'PBO':>6s} {'G6':>6s}")
    lines.append(hdr)
    lines.append("-" * len(hdr))
    for r in c["table"]:
        gp = r["gate_pass_rates"]
        lines.append(f"{r['edge']:22s} {r['net_mean_r']:>+11.3f} "
                     f"{r['pass_rate_all']:>6.2f} "
                     f"{gp['G1']:>6.2f} {gp['G3']:>6.2f} {gp['G4']:>6.2f} "
                     f"{gp['G5_dsr']:>6.2f} {gp['G5_pbo']:>6.2f} {gp['G6']:>6.2f}")
    lines.append("-" * len(hdr))
    lines.append("(pass rates are fractions of seeds; ALL = every gate G1..G6 passed)")
    lines.append("DSR/PBO are the G5 sub-gates. Mean values per edge:")
    for r in c["table"]:
        lines.append(f"  {r['edge']:22s} mean DSR={r['mean_dsr']:.3f}  mean PBO={r['mean_pbo']:.3f}")
    lines.append("")
    lines.append("G2 leakage: N/A by construction (injected i.i.d. edge has no look-ahead).")
    return "\n".join(lines)


def _calibration_verdict(c: dict) -> str:
    """The explicit miscalibration check the task requires (report, never change)."""
    sharpe10 = next(r for r in c["table"] if r["edge"] == "Sharpe 1.0")
    sharpe15 = next(r for r in c["table"] if r["edge"] == "Sharpe 1.5")
    sharpe05 = next(r for r in c["table"] if r["edge"] == "Sharpe 0.5")
    null_ctrl = next(r for r in c["table"] if r["edge"].startswith("Sharpe 0.0"))
    pbo_pinned = all(r["mean_pbo"] > 0.40 for r in c["table"])
    lines = []

    # 1. The primary miscalibration trigger from the task spec.
    if sharpe10["pass_rate_all"] < 0.5:
        lines.append(
            "MISCALIBRATION: a Sharpe-1.0 edge passes only "
            f"{sharpe10['pass_rate_all']:.1%} of the time — the gate thresholds are "
            "too stringent for this account size and would reject a clearly "
            "tradeable edge. RECOMMEND revising thresholds (documented here, NOT "
            "changed by this harness).")
    else:
        lines.append(
            f"Sharpe-1.0 edge detected {sharpe10['pass_rate_all']:.1%} of the time "
            "-> adequately powered for a Sharpe-1.0 edge at this sample size.")

    # 2. The binding-gate diagnosis (the actionable root cause).
    if pbo_pinned and sharpe15["gate_pass_rates"]["G5_pbo"] == 0.0:
        lines.append(
            "ROOT CAUSE — G5 PBO sub-gate is a rank-scatter artifact for SINGLE "
            "strategies: cpcv_harness.compute_pbo compares adjacent fold Sharpes "
            "of ONE strategy, which are randomly scattered for any stationary edge, "
            f"so PBO is pinned near {sharpe15['mean_pbo']:.2f} (>0.30) for EVERY "
            "edge — including Sharpe-1.5 (DSR=1.0, 10th-pct PF>1.0). The PBO<=0.30 "
            "threshold is therefore UNREACHABLE for single-strategy evaluation, "
            "and every candidate fails G5 on PBO regardless of true edge. "
            "RECOMMEND: apply PBO only when choosing AMONG multiple configurations "
            "(its intended use, per the compute_pbo docstring), or drop/repair the "
            "single-strategy approximation — not a threshold tweak.")

    # 3. DSR sub-gate power (the threshold that DOES discriminate).
    if sharpe05["gate_pass_rates"]["G5_dsr"] < 0.5 and sharpe10["gate_pass_rates"]["G5_dsr"] >= 0.5:
        lines.append(
            f"NOTE: the DSR sub-gate (>=0.95, deflated by N={c['config']['n_trials_ledger']}) "
            f"detects Sharpe-1.0 ({sharpe10['gate_pass_rates']['G5_dsr']:.1%}) but NOT "
            f"Sharpe-0.5 ({sharpe05['gate_pass_rates']['G5_dsr']:.1%}) — a Sharpe-0.5 edge "
            f"(+{sharpe05['net_mean_r']:.2f}R/trade net) sits below the search-deflated "
            "MDE. Consider whether DSR>=0.95 is too strict relative to the economic "
            "value of a +0.4R/trade edge at $10K.")

    # 4. False-positive control.
    if null_ctrl["pass_rate_all"] > 0.05:
        lines.append(
            f"WARNING: null control passes {null_ctrl['pass_rate_all']:.1%} of the time "
            "(>5%) — thresholds are too LOOSE (false positives).")
    else:
        lines.append(
            f"Null control false-positive rate {null_ctrl['pass_rate_all']:.1%} (<=5%) "
            "-> no evidence of overly-loose thresholds.")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="Gauntlet power calibration (US-06 M-4)")
    ap.add_argument("--quick", action="store_true",
                    help="30 seeds/edge (fast smoke test)")
    ap.add_argument("--n-trades", type=int, default=300,
                    help="trades per run (default 300)")
    ap.add_argument("--seeds", type=int, default=200,
                    help="Monte Carlo seeds per edge (default 200)")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    n_seeds = 30 if args.quick else args.seeds
    closes = load_real_prices(BASE_TICKER)
    c = calibrate(args.n_trades, n_seeds, closes)

    if args.json:
        print(json.dumps(c, indent=2, default=str))
    else:
        print(_fmt_text(c))
        print()
        print(_calibration_verdict(c))
    return 0


if __name__ == "__main__":
    sys.exit(main())
