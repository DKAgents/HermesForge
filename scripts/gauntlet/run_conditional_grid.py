"""run_conditional_grid.py — apply the conditional-edge grid to two near-misses.

Backtester driver (read-only research, LIVE off, no leverage, no look-ahead).

Re-runs the SIGNAL of each near-miss (NO parameter re-tuning — reuses xsmom.py and
revalidate_hyp21* verbatim), decomposes each into per-regime x per-asset net
rows, and emits the full matrix via conditional_grid.build_grid.

 1. xsmom  (cross-sectional momentum; G3-pass / G4-G5-fail) — shipping config
    kappa=0.5, band=0.25, weekly rebalance, top-quintile long leg.
 2. OI-level composite (HYP-21 C-positioning = z(OI-change7d) + z(OI-level90d);
    gross +48bps net at correct cost, failed G4/G5) — long/short decile.

Cost (single source: fee_source, realistic 4.5bps taker/leg):
  * one position round-trip = 12 bps  (4.5*2 taker + 2.5 slip + 0.5 funding)
    -> charged per NAME row (single-name net).
  * xsmom portfolio net uses the sim's own turnover cost (already inside net_r).
  * OI portfolio net uses 24 bps both-legs (2-position spread), the DECISION cost.

No look-ahead:
  * xsmom signal uses closes through t-1 (skip=1 momentum + overlay lookback=1);
    regime is read as of t-1 (regime series shifted by 1 day).
  * OI signal uses closes through t (next-open fill at open[t+1]); regime read
    as of t.
  * OI hold=5 uses a NON-OVERLAPPING stride-5 resample (the honest OOS sample,
    matching the correct-cost report), so cell "count" = independent rebalances.

Writes ONE trials-ledger entry per strategy (fresh param_hash incl. the regime
definition + cost model). Path-scoped commit only.

Usage: python3 run_conditional_grid.py [--no-write]
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import pathlib
import sys

import numpy as np
import pandas as pd

_THIS_DIR = pathlib.Path(__file__).resolve().parent          # scripts/gauntlet
for _p in (_THIS_DIR, str(_THIS_DIR.parent)):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import trials_ledger as ledger                                 # noqa: E402
import xsmom as x                                              # noqa: E402
import conditional_grid as cg                                  # noqa: E402
import revalidate_xsmom as rx                                  # noqa: E402
import revalidate_hyp21_multifactor_composite as h21           # noqa: E402

# ── cost model (single source: fee_source) ───────────────────────────────────
COST_ONE_POSITION_BPS = 12.0        # 4.5*2 taker + 2.5 slip + 0.5 funding
COST_BOTH_LEGS_BPS = 24.0           # OI spread = long + short (2 positions)


# ── xsmom ────────────────────────────────────────────────────────────────────

def xsmom_rows(panel, btc, regime: pd.Series, eps) -> list[dict]:
    """Emit portfolio + name rows for xsmom. Name rows re-derive the long-leg
    membership with xsmom's OWN public functions (no sim modification)."""
    # regime shifted: signal uses closes through t-1 -> regime through t-1
    regime_shifted = regime.shift(1)

    # precompute momentum / vol exactly as simulate_xsmom does
    names = list(panel.columns)
    C = panel.to_numpy(dtype=float).T                     # (N, T)
    btc_arr = btc.reindex(panel.index).to_numpy(dtype=float)
    n_names, T = C.shape
    mom = np.full((n_names, T), np.nan)
    vol = np.full((n_names, T), np.nan)
    for i in range(n_names):
        mom[i] = x.momentum_series(pd.Series(C[i]), skip=x.MOMENTUM_SKIP_DAYS,
                                   lookback=x.MOMENTUM_LOOKBACK_DAYS).to_numpy(float)
        vol[i] = x.realized_vol_daily(pd.Series(C[i]),
                                      lookback=x.VOL_LOOKBACK_DAYS).to_numpy(float)
    # date index for regime lookups + forward return basis
    ts_days = pd.Series(panel.index)
    start = x.BTC_DMA_WINDOW + 1

    rows = []

    # (a) portfolio rows: from the shipped sim episodes
    for _, e in eps.iterrows():
        reb_ms = int(e["reb_ts"])
        d = pd.to_datetime(reb_ms, unit="ms").normalize()
        rows.append({
            "strategy": "xsmom", "trade_date": d, "coin": "ALL",
            "level": "portfolio",
            "net_r": float(e["net_return"]) * 1e4,      # fraction -> bps
            "gross_r": float(e["gross_return"]) * 1e4,
        })

    # (b) name rows: long-leg membership at each rebalance + 7d forward return
    for t in range(start, T):
        if (t - start) % x.REBALANCE_PERIOD != 0:
            continue
        overlay_up = x.btc_200dma_overlay(pd.Series(btc_arr), t)
        gross_target = x.LONG_GROSS_UP if overlay_up else x.LONG_GROSS_UP * x.DOWN_SCALE
        moms = pd.Series(mom[:, t], index=names)
        vols = pd.Series(vol[:, t], index=names)
        wstar, _ = x.target_weights(moms, vols, gross_target,
                                    top_frac=x.TOP_FRAC,
                                    max_name_weight=x.MAX_NAME_WEIGHT)
        if t + x.REBALANCE_PERIOD >= T:
            continue
        d = ts_days.iloc[t]
        for name in wstar:
            i = names.index(name)
            p0 = C[i, t]
            p1 = C[i, t + x.REBALANCE_PERIOD]
            if not (np.isfinite(p0) and np.isfinite(p1) and p0 > 0):
                continue
            fwd = p1 / p0 - 1.0
            rows.append({
                "strategy": "xsmom", "trade_date": d, "coin": name,
                "level": "name",
                "gross_r": fwd * 1e4,
                "net_r": (fwd - COST_ONE_POSITION_BPS / 1e4) * 1e4,
            })

    return rows, regime_shifted


# ── OI-level composite (HYP-21 C-positioning) ────────────────────────────────

def oi_rows(opens, closes, ois, regime: pd.Series) -> list[dict]:
    """Emit portfolio + name rows for C-positioning (long/short decile)."""
    oi_log = np.log(ois.replace(0.0, np.nan))
    close_log = np.log(closes.replace(0.0, np.nan))
    f_oi_change = oi_log - oi_log.shift(h21.OI_CHANGE_LOOKBACK)
    oi_mean90 = ois.shift(1).rolling(h21.OI_LEVEL_WINDOW,
                                     min_periods=h21.OI_LEVEL_WINDOW).mean()
    oi_std90 = ois.shift(1).rolling(h21.OI_LEVEL_WINDOW,
                                    min_periods=h21.OI_LEVEL_WINDOW).std()
    f_oi_level_ts = (ois - oi_mean90) / oi_std90.replace(0.0, np.nan)
    z_oi_change = h21.xs_zscore(f_oi_change)
    z_oi_level = h21.xs_zscore(f_oi_level_ts)
    signal = z_oi_change + z_oi_level                      # C-positioning

    cols = [c for c in signal.columns if c in opens.columns]
    sig = signal[cols]
    opens_sub = opens[cols]

    rows = []
    for hold in (1, 5):
        entry = opens_sub.shift(-1)
        exitp = opens_sub.shift(-(1 + hold))
        fwd = exitp / entry - 1.0
        common = sig.index.intersection(opens_sub.index)
        sig_c = sig.loc[common]
        fwd_c = fwd.loc[common]
        dates = list(sig_c.index)
        stride = 1 if hold <= 1 else hold
        for t in range(len(dates) - (1 + hold)):
            if t % stride != 0:                            # non-overlap resample
                continue
            s = sig_c.iloc[t].to_numpy(dtype=float)
            f = fwd_c.iloc[t].to_numpy(dtype=float)
            mask = np.isfinite(s) & np.isfinite(f)
            if mask.sum() < h21.MIN_COINS_DAY:
                continue
            s_v = s[mask]; f_v = f[mask]
            coin_idx = np.array(cols)[mask]
            order = np.argsort(s_v)
            n = len(s_v)
            k = max(1, n // 10)
            bot = order[:k]
            top = order[-k:]
            long_ret = float(np.mean(f_v[top]))
            short_ret = float(np.mean(f_v[bot]))
            gross = long_ret - short_ret
            net = gross - COST_BOTH_LEGS_BPS / 1e4
            d = dates[t]
            rows.append({
                "strategy": f"OI-level-hold{hold}", "trade_date": d, "coin": "ALL",
                "level": "portfolio",
                "gross_r": gross * 1e4, "net_r": net * 1e4,
            })
            for idx in top:
                fv = float(f_v[idx])
                rows.append({
                    "strategy": f"OI-level-hold{hold}", "trade_date": d,
                    "coin": str(coin_idx[idx]), "level": "name",
                    "gross_r": fv * 1e4,
                    "net_r": fv * 1e4 - COST_ONE_POSITION_BPS,
                })
            for idx in bot:
                fv = float(f_v[idx])
                rows.append({
                    "strategy": f"OI-level-hold{hold}", "trade_date": d,
                    "coin": str(coin_idx[idx]), "level": "name",
                    "gross_r": -fv * 1e4,
                    "net_r": -fv * 1e4 - COST_ONE_POSITION_BPS,
                })
    return rows


# ── reporting ────────────────────────────────────────────────────────────────


def _payload(sr: dict) -> dict:
    """Extract ledger-ready summary from one strategy's grid sub-dict."""
    return {
        "regime_portfolio": sr["regime_portfolio"],
        "regime_counts": sr["regime_counts"],
        "asset_marginal": sr["asset_marginal"],
        "cells": sr["cells"],
    }


def _ph(sid: str) -> str:
    param_dict = {
        "construction": "conditional_edge_grid",
        "regime_definition": "btc_200d_sma_trend",
        "sma_window": cg.SMA_WINDOW, "band": cg.BAND,
        "regime_tags": ["risk_on", "risk_off", "range"],
        "cost_one_position_bps": COST_ONE_POSITION_BPS,
        "cost_both_legs_bps": COST_BOTH_LEGS_BPS,
        "strategy": sid,
    }
    return hashlib.sha256(json.dumps(param_dict, sort_keys=True).encode()).hexdigest()


def _fmt_mat(grid: dict, strategy: str, top_n: int = 15) -> str:
    sr = grid[strategy]
    lines = []
    lines.append(f"\n##### {strategy} — per-regime x per-asset matrix #####")

    # regime counts
    lines.append("regime sample-size split (holding periods per regime):")
    for r, n in sorted(sr["regime_counts"].items()):
        lines.append(f"    {r:9s} n={n}")

    # per-regime PORTFOLIO net (official)
    lines.append("\n(a) per-regime net (PORTFOLIO, official strategy P&L):")
    lines.append(f"    {'regime':9s} {'n':>5s} {'net_total':>12s} {'PF':>8s} {'win%':>7s}")
    for r, m in sorted(sr["regime_portfolio"].items()):
        lines.append(f"    {r:9s} {m['n']:5d} {m['net_total']:+12.1f} "
                     f"{m['pf']:8.2f} {m['win_rate']*100:7.1f}")

    # per-regime NAME net (sum of per-name attribution)
    lines.append("\n   per-regime net (sum of per-name single-name nets):")
    for r, m in sorted(sr["regime_name"].items()):
        lines.append(f"    {r:9s} n={m['n']:5d} net={m['net_total']:+12.1f} "
                     f"PF={m['pf']:8.2f} win%={m['win_rate']*100:6.1f}")

    # per-asset net (question b) — top coins by trade count
    lines.append(f"\n(b) per-asset net (top {top_n} coins by trade count):")
    lines.append(f"    {'coin':10s} {'n':>5s} {'net_total':>12s} {'PF':>8s} {'win%':>7s}")
    for coin, m in list(sr["asset_marginal"].items())[:top_n]:
        lines.append(f"    {coin:10s} {m['n']:5d} {m['net_total']:+12.1f} "
                     f"{m['pf']:8.2f} {m['win_rate']*100:7.1f}")
    n_coins = len(sr["asset_marginal"])
    if n_coins > top_n:
        rest = list(sr["asset_marginal"].items())[top_n:]
        tot = sum(m["net_total"] for _, m in rest)
        n_rest = sum(m["n"] for _, m in rest)
        lines.append(f"    {'(rest)':10s} {n_rest:5d} {tot:+12.1f}  "
                     f"(remaining {n_coins - top_n} coins)")

    # full cell matrix (question c) — top coins per regime
    lines.append("\n(c) per-regime x per-asset cells (net_total, n in parens):")
    for r in sorted(sr["cells"]):
        cells = sr["cells"][r]
        lines.append(f"  regime={r}:")
        for coin, m in list(cells.items())[:top_n]:
            lines.append(f"      {coin:10s} net={m['net_total']:+10.1f} "
                         f"PF={m['pf']:7.2f} win%={m['win_rate']*100:6.1f} (n={m['n']})")
        if len(cells) > top_n:
            lines.append(f"      ... {len(cells) - top_n} more coins in this regime")

    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-write", action="store_true")
    args = ap.parse_args()

    print("=== conditional-edge grid: xsmom + OI-level (HYP-21 C-positioning) ===\n")
    regime = cg.compute_regime(cg.load_btc_daily())
    print(f"BTC regime series: {regime.dropna().value_counts().to_dict()} "
          f"(n={int(regime.notna().sum())} days classified, "
          f"from {regime.first_valid_index().date()})")

    # ── xsmom ────────────────────────────────────────────────────────────────
    print("\n--- xsmom: fetch HL 1d bars + run shipped sim ---")
    daily = rx.load_all_daily(rx.BACKTEST_UNIVERSE)
    panel, btc, _meta = rx.build_panel(daily)
    nav, eps, _diag = x.simulate_xsmom(panel, btc)
    print(f"  panel {panel.shape[0]}d x {panel.shape[1]} names; "
          f"episodes={len(eps)}  mean_net_r={eps['net_r'].mean():+.4f}")
    xrows, xregime = xsmom_rows(panel, btc, regime, eps)

    # ── OI-level ─────────────────────────────────────────────────────────────
    print("\n--- OI-level (HYP-21 C-positioning): load OI + build composite ---")
    opens, closes, ois = h21.load_oi_daily()
    print(f"  OI panel {opens.shape[0]}d x {opens.shape[1]} coins")
    orows = oi_rows(opens, closes, ois, regime)

    # ── build grids ──────────────────────────────────────────────────────────
    grid_x = cg.build_grid(xrows, xregime)
    grid_o = cg.build_grid(orows, regime)

    # ── report ───────────────────────────────────────────────────────────────
    print(_fmt_mat(grid_x, "xsmom", top_n=15))
    print(_fmt_mat(grid_o, "OI-level-hold1", top_n=15))
    print(_fmt_mat(grid_o, "OI-level-hold5", top_n=15))

    # ── write trials (one per strategy, fresh param_hash) ────────────────────
    if not args.no_write:
        n = ledger.count()
        period_oi = [str(opens.index.min().date()), str(opens.index.max().date())]
        period_x = [str(panel.index.min().date()), str(panel.index.max().date())]
        ui_x = sorted(panel.columns.tolist())
        ui_o = sorted(opens.columns.tolist())
        for sid, period, universe, result_payload, ph in [
            ("XSMOM-COND", period_x, ui_x, _payload(grid_x["xsmom"]), _ph("XSMOM-COND")),
            ("HYP21-COND", period_oi, ui_o,
             {"hold_1d": _payload(grid_o["OI-level-hold1"]),
              "hold_5d": _payload(grid_o["OI-level-hold5"])},
             _ph("HYP21-COND")),
        ]:
            uh = hashlib.sha256(",".join(universe).encode()).hexdigest()
            result = {
                "strategy": sid,
                "regime_definition": "btc_200d_sma_trend",
                "sma_window": cg.SMA_WINDOW, "band": cg.BAND,
                "regime_tags": ["risk_on", "risk_off", "range"],
                "cost_one_position_bps": COST_ONE_POSITION_BPS,
                "cost_both_legs_bps": COST_BOTH_LEGS_BPS,
                "no_lookahead": True, "leverage": "none", "live": "off",
                "data_source": "hl_oi_hf parquet (BTC regime) + HL 1d bars (xsmom)",
                **result_payload,
            }
            e = ledger.increment_trial(sid, ph, uh, period[0], period[1], result)
            print(f"\n  wrote trial {sid}: param_hash={ph[:16]}...")
    else:
        print("\n[--no-write] skipped ledger entries")

    print("\nDone.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
