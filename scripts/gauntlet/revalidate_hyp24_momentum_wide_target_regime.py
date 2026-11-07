"""revalidate_hyp24_momentum_wide_target_regime.py — HYP-24 combined-lever test.

Momentum (cross-sectional 7d) x WIDE target (3R) x REGIME (BTC 200d SMA).
This COMBINES two prior findings and tests them together:
  * HYP-23: a WIDE (3R) target beats a tight (1R) target for NET (tight target
    = fee tax on the weak drift). Part of that gain is log-normal geometry.
  * HYP-22: REGIME conditions the signal (continuation was a bear-regime
    artifact; it reversed in bull).

The open question (pre-registered, FIXED): does momentum + 3R target become
NET-POSITIVE in a SPECIFIC regime?

Pre-registered operationalization (fixed, no tuning):
  * Signal: cross-sectional 7d price momentum, long top-decile / short
    bottom-decile.
  * Stop: 2x ATR14 (= 1R).  Target: 3R (FIXED — the HYP-23 wide target).
  * Regime: BTC 200d SMA on the CLEANED series (hl_oi_hf_clean/), the
    conditional_grid pre-registered taxonomy (BAND=0.03; risk_on = above band +
    SMA rising, risk_off = below band, else range).
  * Cost: 4.5 bps/leg taker + 2.5 bps adverse entry slip + hourly funding
    (longs pay positive funding).
  * Exit resolution: HOURLY first-touch (NOT daily both-touched).

HONESTY GATE: a ZERO-DRIFT synthetic control is run alongside. Far-target gross
gains are partly a log-normal geometric tilt with ZERO alpha; a regime cell
counts ONLY if it (a) beats the same cell in the control (net > control net),
(b) has adequate sample, and (c) is economically motivated.

Zero-drift control: per-coin HOURLY log-returns are demeaned (drift removed,
realized volatility + intraday structure preserved) and re-compounded from the
real first price -> a zero-drift synthetic hourly path. The IDENTICAL pipeline
(momentum signal, 2xATR stop, 3R target, hourly first-touch, fees+funding) runs
on it; daily OHLC/ATR/momentum are re-derived from the synthetic hourly path.
The REGIME split is unchanged (real BTC) — regime is a market-state property,
not a per-coin drift.

Driver writes ONE trials-ledger entry (the real run; the control is a
diagnostic, not a separate trial).  Read-only on live state; LIVE off.

Usage: python3 revalidate_hyp24_momentum_wide_target_regime.py [--no-write]
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

_THIS_DIR = pathlib.Path(__file__).resolve().parent          # scripts/gauntlet
for _p in (_THIS_DIR, str(_THIS_DIR.parent)):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import conditional_grid as cgrid                       # noqa: E402
import trials_ledger as ledger                         # noqa: E402

OI_DIR = pathlib.Path.home() / ".hermes" / "market_data" / "hl_oi_hf"
CLEAN_DIR = pathlib.Path.home() / ".hermes" / "market_data" / "hl_oi_hf_clean"
FUNDING_DIR = pathlib.Path.home() / ".hermes" / "market_data" / "hl_funding_hf"

# ── Pre-registered constants (FIXED — do not tune) ──────────────────────────
DECILE_FRAC = 0.10
MOMENTUM_LOOKBACK = 7
ATR_WINDOW = 14
STOP_ATR_MULT = 2.0        # stop distance = 2x ATR = 1R
TARGET_R = 3.0             # FIXED — the HYP-23 wide target
TAKER_BPS = 4.5
ENTRY_SLIP_BPS = 2.5
TIMESTOP_BARS = 20
MIN_COINS_DAY = 20


def _load_mark_panel(directory: pathlib.Path, columns=None):
    files = sorted(glob.glob(str(directory / "*.parquet")))
    if not files:
        raise SystemExit(f"no parquet under {directory}")
    cols = columns or ["timestamp", "coin", "dex", "mark_price"]
    parts = [pd.read_parquet(f, columns=cols) for f in files]
    df = pd.concat(parts, ignore_index=True)
    native = df[(df["dex"] == "")].dropna(subset=["mark_price"])
    native["timestamp"] = native["timestamp"].dt.tz_convert("UTC")
    native["date"] = native["timestamp"].dt.normalize()
    return native


def load_daily_ohlc() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame,
                                pd.DataFrame]:
    """Hourly mark_price -> daily OHLC panels (native perps, hl_oi_hf)."""
    native = _load_mark_panel(OI_DIR)
    daily = (native.sort_values("timestamp")
             .groupby(["coin", "date"], sort=False)
             .agg(open=("mark_price", "first"), high=("mark_price", "max"),
                  low=("mark_price", "min"), close=("mark_price", "last"))
             .reset_index())
    start, end = daily["date"].min(), daily["date"].max()
    cal = pd.date_range(start, end, freq="D", tz="UTC")
    opens = daily.pivot(index="date", columns="coin", values="open").reindex(cal)
    highs = daily.pivot(index="date", columns="coin", values="high").reindex(cal)
    lows = daily.pivot(index="date", columns="coin", values="low").reindex(cal)
    closes = daily.pivot(index="date", columns="coin", values="close").reindex(cal)
    return opens, highs, lows, closes


def load_hourly_marks(coins, directory=OI_DIR) -> tuple[np.ndarray, list]:
    """Hourly mark_price -> (n_coins x n_hours) panel + date-normalized day list."""
    native = _load_mark_panel(directory)
    native = native[native["coin"].isin(coins)]
    native["h"] = native["timestamp"].dt.floor("h")
    keep = (native.sort_values("timestamp")
            .drop_duplicates(subset=["h", "coin"], keep="last"))
    panel = keep.pivot(index="h", columns="coin", values="mark_price")
    hr_idx = pd.date_range(panel.index.min(), panel.index.max(), freq="h", tz="UTC")
    panel = panel.reindex(hr_idx)
    return panel[coins].to_numpy(dtype=float).T, list(hr_idx.normalize())


def load_daily_funding() -> pd.DataFrame:
    """Hourly funding_rate -> daily SUM panel (native perps)."""
    files = sorted(glob.glob(str(FUNDING_DIR / "*.parquet")))
    if not files:
        raise SystemExit(f"no funding parquet under {FUNDING_DIR}")
    parts = [pd.read_parquet(f, columns=["timestamp", "coin", "dex", "funding_rate"])
             for f in files]
    df = pd.concat(parts, ignore_index=True)
    native = df[(df["dex"] == "")].dropna(subset=["funding_rate"])
    native["timestamp"] = native["timestamp"].dt.tz_convert("UTC")
    native["date"] = native["timestamp"].dt.normalize()
    daily = (native.sort_values("timestamp")
             .groupby(["coin", "date"], sort=False)
             .agg(fund_sum=("funding_rate", "sum")).reset_index())
    start, end = daily["date"].min(), daily["date"].max()
    cal = pd.date_range(start, end, freq="D", tz="UTC")
    return daily.pivot(index="date", columns="coin", values="fund_sum").reindex(cal)


def load_btc_cleaned() -> pd.Series:
    """BTC native-perp daily close from the CLEANED series (hl_oi_hf_clean/)."""
    native = _load_mark_panel(CLEAN_DIR)
    btc = native[native["coin"] == "BTC"]
    daily = (btc.sort_values("timestamp")
             .groupby("date", sort=True)["mark_price"].last())
    daily = daily[~daily.index.duplicated(keep="last")].sort_index()
    return daily


def indicators(opens, highs, lows, closes):
    """Return O,H,L,C arrays + ATR14 + 7d momentum (coins x days)."""
    coins = list(closes.columns)
    prev_close = closes.shift(1)
    tr = pd.DataFrame(np.maximum.reduce([
        (highs - lows).to_numpy(dtype=float),
        (highs - prev_close).abs().to_numpy(dtype=float),
        (lows - prev_close).abs().to_numpy(dtype=float),
    ]), index=closes.index, columns=closes.columns)
    atr = tr.rolling(ATR_WINDOW, min_periods=ATR_WINDOW).mean()
    mom = closes / closes.shift(MOMENTUM_LOOKBACK) - 1.0

    def arr(df):
        return df.to_numpy(dtype=float).T
    return coins, arr(opens), arr(highs), arr(lows), arr(closes), arr(atr), arr(mom)


def zero_drift_panel(Mh: np.ndarray) -> np.ndarray:
    """Per-coin ZERO-DRIFT hourly panel (cumsum-anchored).

    For each coin, demean its realized hourly log-returns (drift -> 0, realized
    volatility + intraday structure preserved) and re-compound from its real
    first price. The panel is used ONLY as a ratio syn[c,h]/syn[c,h0] inside
    run_trades to re-anchor the zero-drift forward path at each trade's REAL
    entry — so the control keeps real entries/ATR/fees and only removes drift.
    """
    out = np.full_like(Mh, np.nan)
    for c in range(Mh.shape[0]):
        p = Mh[c]
        finite = np.isfinite(p)
        if finite.sum() < 8:
            continue
        idx = np.where(finite)[0]
        pv = p[idx]
        lr = np.diff(np.log(np.maximum(pv, 1e-12)))
        lr = lr - lr.mean()
        cum = np.concatenate(([0.0], np.cumsum(lr)))
        out[c, idx] = pv[0] * np.exp(cum)
    return out


def run_trades(Mh, C, F, ATR, M, dates, coins, day_to_first, hour_to_day,
               syn_panel=None, day_to_last=None):
    """Run momentum + 3R-target backtest. Returns list of trade record dicts.

    When `syn_panel` (a per-coin ZERO-DRIFT hourly panel, cumsum-anchored) is
    provided, the ENTRY, stop/target levels, ATR sizing, fees and the coins
    selected are IDENTICAL to the real run — ONLY the forward price path is
    replaced by the zero-drift path anchored at the real entry:

        mark(h) = entry * syn_panel[c,h] / syn_panel[c,start_h]

    This is the "same trades, zero-drift market" control: it isolates the
    log-normal geometric tilt (geometry) from momentum's drift (alpha), while
    keeping cost structure and sample EXACTLY matched to the real run.
    """
    n_coins, n_days = C.shape
    n_hours = Mh.shape[1]
    records = []
    fees_frac = (2.0 * TAKER_BPS + ENTRY_SLIP_BPS) / 1e4
    max_hours = TIMESTOP_BARS * 24

    def mark(c, h, base_h):
        if syn_panel is None:
            return Mh[c, h]
        b = syn_panel[c, base_h]
        s = syn_panel[c, h]
        if not (np.isfinite(b) and np.isfinite(s) and b > 0):
            return np.nan
        return Mh[c, base_h] * (s / b)

    for t in range(0, n_days - 1):
        mom_t = M[:, t]
        atr_t = ATR[:, t]
        close_t = C[:, t]
        valid = (np.isfinite(mom_t) & np.isfinite(atr_t) & np.isfinite(close_t)
                 & (atr_t > 0))
        if valid.sum() < MIN_COINS_DAY:
            continue
        start_h = day_to_first.get(dates[t + 1])
        if start_h is None:
            continue
        entry_col = Mh[:, start_h]
        valid &= np.isfinite(entry_col) & (entry_col > 0)
        if valid.sum() < MIN_COINS_DAY:
            continue

        idx = np.where(valid)[0]
        mvals = mom_t[idx]
        order = np.argsort(mvals)
        n = len(order)
        k = max(1, int(n * DECILE_FRAC))
        bot_idx = idx[order[:k]]
        top_idx = idx[order[-k:]]
        cands = [(c, +1) for c in top_idx] + [(c, -1) for c in bot_idx]

        for c, direction in cands:
            entry = Mh[c, start_h]
            risk = 2.0 * atr_t[c]
            risk_pct = risk / entry
            if not (risk_pct > 0) or not np.isfinite(risk_pct):
                continue
            if direction > 0:
                stop = entry - risk
                target = entry + TARGET_R * risk
            else:
                stop = entry + risk
                target = entry - TARGET_R * risk

            kind = None
            exit_h = None
            end_h = min(start_h + 1 + max_hours, n_hours)
            for h in range(start_h + 1, end_h):
                m = mark(c, h, start_h)
                if not np.isfinite(m):
                    continue
                if direction > 0:
                    if m <= stop:
                        kind, exit_h = "stop", h
                        break
                    if m >= target:
                        kind, exit_h = "target", h
                        break
                else:
                    if m >= stop:
                        kind, exit_h = "stop", h
                        break
                    if m <= target:
                        kind, exit_h = "target", h
                        break

            if kind is None:
                kind = "time"
                exit_day = min(t + TIMESTOP_BARS, n_days - 1)
                if not np.isfinite(C[c, exit_day]):
                    continue
            else:
                exit_day = int(hour_to_day[exit_h])
                if exit_day < 0:
                    continue

            if kind == "target":
                gross_r = TARGET_R
            elif kind == "stop":
                gross_r = -1.0
            else:
                if syn_panel is not None and day_to_last is not None:
                    close_h = day_to_last.get(dates[exit_day])
                    epx = (mark(c, close_h, start_h) if close_h is not None
                           else np.nan)
                else:
                    epx = C[c, exit_day]
                if not np.isfinite(epx) or not (epx > 0):
                    continue
                gross_r = ((epx - entry) / entry / risk_pct if direction > 0
                           else (entry - epx) / entry / risk_pct)

            fund_frac = 0.0
            for b in range(t + 1, exit_day + 1):
                fv = F[c, b]
                if np.isfinite(fv):
                    fund_frac += fv
            funding_r = -direction * fund_frac / risk_pct
            fee_r = fees_frac / risk_pct
            net_r = gross_r - fee_r + funding_r

            records.append({
                "strategy": "momentum_3R",
                "trade_date": dates[t],
                "coin": coins[c],
                "direction": int(direction),
                "kind": kind,
                "gross_r": float(gross_r),
                "fee_r": float(fee_r),
                "funding_r": float(funding_r),
                "net_r": float(net_r),
                "bars_held": exit_day - t,
                "risk_pct": float(risk_pct),
                "level": "name",
            })
    return records


def _pf(rs):
    gains = sum(r for r in rs if r > 0)
    losses = abs(sum(r for r in rs if r < 0))
    return gains / losses if losses > 0 else (float("inf") if gains > 0 else 0.0)


def _stats(records):
    if not records:
        return {"n_trades": 0}
    net = np.array([r["net_r"] for r in records])
    gross = np.array([r["gross_r"] for r in records])
    fee = np.array([r["fee_r"] for r in records])
    fund = np.array([r["funding_r"] for r in records])
    wins = net > 0
    pos = float(net[wins].sum()) if wins.any() else 0.0
    neg = float(-net[~wins].sum()) if (~wins).any() else 0.0
    return {
        "n_trades": int(len(records)),
        "mean_net_r": float(net.mean()),
        "median_net_r": float(np.median(net)),
        "total_net_r": float(net.sum()),
        "win_rate": float(wins.mean()),
        "pf": pos / neg if neg > 0 else (float("inf") if pos > 0 else 0.0),
        "mean_gross_r": float(gross.mean()),
        "mean_fee_r": float(fee.mean()),
        "mean_funding_r": float(fund.mean()),
        "exit_breakdown": {k: int(sum(1 for r in records if r["kind"] == k))
                           for k in ("target", "stop", "time")},
    }


def cell_table(real_grid, ctrl_grid):
    """Compare per-regime and per-(regime,asset) mean net R: real vs control.

    Uses `name`-level attribution (`regime_name` for the regime row, `cells` for
    the per-regime x per-asset matrix), since every holding period here is a
    single coin position (no separate book-level `portfolio` row exists).
    """
    regimes = ("risk_on", "risk_off", "range")
    out = {"regime": {}, "cells": {}}
    for reg in regimes:
        rp = real_grid.get("regime_name", {}).get(reg)
        cp = ctrl_grid.get("regime_name", {}).get(reg)
        if rp is None or cp is None:
            continue
        out["regime"][reg] = {
            "n": rp["n"],
            "real_mean": rp["net_total"] / rp["n"] if rp["n"] else 0.0,
            "ctrl_mean": cp["net_total"] / cp["n"] if cp["n"] else 0.0,
            "real_pf": rp["pf"], "ctrl_pf": cp["pf"],
            "real_win": rp["win_rate"], "ctrl_win": cp["win_rate"],
        }
        rc = real_grid.get("cells", {}).get(reg, {})
        cc = ctrl_grid.get("cells", {}).get(reg, {})
        for coin in rc:
            rcell = rc[coin]
            ccell = cc.get(coin)
            real_mean = rcell["net_total"] / rcell["n"] if rcell["n"] else 0.0
            ctrl_mean = (ccell["net_total"] / ccell["n"]
                         if ccell and ccell["n"] else 0.0)
            out["cells"].setdefault(reg, []).append({
                "coin": coin, "n": rcell["n"],
                "real_mean": real_mean, "ctrl_mean": ctrl_mean,
                "delta": real_mean - ctrl_mean,
                "real_pf": rcell["pf"],
            })
    for reg in list(out["cells"]):
        out["cells"][reg].sort(key=lambda c: -c["n"])
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-write", action="store_true")
    args = ap.parse_args()

    print("=== HYP-24 — momentum x wide-target x regime (combined) ===\n")

    print("loading daily OHLC + funding (real) ...")
    opens, highs, lows, closes = load_daily_ohlc()
    fundsum = load_daily_funding()
    common = [c for c in closes.columns if c in fundsum.columns]
    closes = closes[common]; opens = opens[common]
    highs = highs[common]; lows = lows[common]; fundsum = fundsum[common]
    print(f"  {len(common)} coins, {closes.shape[0]} days")
    print(f"  ({closes.index.min().date()} -> {closes.index.max().date()})")

    coins, O, H, L, C, ATR, M = indicators(opens, highs, lows, closes)
    F = fundsum.to_numpy(dtype=float).T
    dates = [pd.Timestamp(d) for d in closes.index]

    print("loading hourly marks (real) ...")
    Mh, hr_days = load_hourly_marks(common, OI_DIR)
    uniq_days, first_idx = np.unique(np.asarray(hr_days, dtype=object),
                                     return_index=True)
    day_to_first = {uniq_days[i]: int(first_idx[i])
                    for i in range(len(uniq_days))}
    # last hourly index of each day (for control time-stop close)
    day_to_last = {}
    for i in range(len(uniq_days)):
        d = uniq_days[i]
        matches = np.where(np.asarray(hr_days, dtype=object) == d)[0]
        if matches.size:
            day_to_last[d] = int(matches[-1])
    date_to_didx = {d: i for i, d in enumerate(dates)}
    hour_to_day = np.array([date_to_didx.get(d, -1) for d in hr_days],
                           dtype=np.int64)
    print(f"  hourly marks: {Mh.shape[0]} coins x {Mh.shape[1]} hours")

    # ── regime (CLEANED BTC) ───────────────────────────────────────────────
    print("classifying regime (BTC 200d SMA, cleaned series) ...")
    btc = load_btc_cleaned()
    regime = cgrid.compute_regime(btc)
    rc = regime.value_counts(dropna=True)
    # regime[t] known at signal close (uses BTC through day t)
    trade_regime = {d: regime.get(d) for d in dates}
    print(f"  regime day counts: "
          f"risk_on {rc.get('risk_on',0)} / risk_off {rc.get('risk_off',0)} / "
          f"range {rc.get('range',0)}  (NaN={int(regime.isna().sum())})")

    # ── REAL run ───────────────────────────────────────────────────────────
    print("running REAL backtest (momentum + 3R target) ...")
    real_records = run_trades(Mh, C, F, ATR, M, dates, coins,
                              day_to_first, hour_to_day)

    # ── ZERO-DRIFT CONTROL run ─────────────────────────────────────────────
    print("building zero-drift panel (demeaned hourly log-returns) ...")
    syn = zero_drift_panel(Mh)
    print("running CONTROL backtest (same trades, zero-drift forward) ...")
    ctrl_records = run_trades(Mh, C, F, ATR, M, dates, coins,
                              day_to_first, hour_to_day,
                              syn_panel=syn, day_to_last=day_to_last)

    # ── grids ──────────────────────────────────────────────────────────────
    real_grid = cgrid.build_grid(real_records, regime)[
        "momentum_3R"] if real_records else {}
    ctrl_grid = cgrid.build_grid(ctrl_records, regime)[
        "momentum_3R"] if ctrl_records else {}

    rs = _stats(real_records)
    cs = _stats(ctrl_records)

    def _rp_diag(records, label):
        rp = np.array([r["risk_pct"] for r in records if r["risk_pct"] > 0])
        fee = np.array([r["fee_r"] for r in records])
        print(f"  {label}: risk_pct mean={np.mean(rp)*100:.2f}% "
              f"median={np.median(rp)*100:.2f}% p10={np.percentile(rp,10)*100:.2f}% "
              f"p90={np.percentile(rp,90)*100:.2f}% "
              f"| fee_r mean={np.mean(fee):.4f} median={np.median(fee):.4f} "
              f"p90={np.percentile(fee,90):.4f}")
    _rp_diag(real_records, "REAL  ")
    _rp_diag(ctrl_records, "CTRL  ")
    print(f"\n  REAL    : n={rs['n_trades']} net={rs['mean_net_r']:+.4f}R "
          f"win={rs['win_rate']:.3f} PF={rs['pf']:.3f} "
          f"gross={rs['mean_gross_r']:+.4f}R exits={rs['exit_breakdown']}")
    print(f"  CONTROL : n={cs['n_trades']} net={cs['mean_net_r']:+.4f}R "
          f"win={cs['win_rate']:.3f} PF={cs['pf']:.3f} "
          f"gross={cs['mean_gross_r']:+.4f}R exits={cs['exit_breakdown']}")

    compare = cell_table(real_grid, ctrl_grid)

    print("\n  per-regime (mean net R/trade): real vs control vs delta")
    print(f"  {'regime':>9s} {'n':>6s} {'real':>8s} {'ctrl':>8s} "
          f"{'delta':>8s} {'PF_real':>8s} {'PF_ctrl':>8s} {'win_real':>8s}")
    for reg in ("risk_on", "risk_off", "range"):
        v = compare["regime"].get(reg)
        if not v:
            continue
        print(f"  {reg:>9s} {v['n']:>6d} {v['real_mean']:>+8.4f} "
              f"{v['ctrl_mean']:>+8.4f} {v['real_mean']-v['ctrl_mean']:>+8.4f} "
              f"{v['real_pf']:>8.3f} {v['ctrl_pf']:>8.3f} {v['real_win']:>8.3f}")

    def _year_grid(records):
        """Mean net R by (calendar year x regime) — robustness of any cell."""
        buckets = {}
        for r in records:
            reg = regime.get(r["trade_date"])
            if reg is None:
                continue
            yr = r["trade_date"].year
            key = (yr, reg)
            buckets.setdefault(key, []).append(r["net_r"])
        return {k: (len(v), float(np.mean(v))) for k, v in buckets.items()}

    print("\n  sub-period robustness (mean net R/trade, REAL, by year x regime):")
    yg = _year_grid(real_records)
    yrs = sorted({k[0] for k in yg})
    regs = ("risk_on", "risk_off", "range")
    print(f"  {'year':>6s} " + " ".join(f"{r:>14s}" for r in regs))
    for yr in yrs:
        row = []
        for reg in regs:
            v = yg.get((yr, reg))
            row.append(f"{v[1]:+8.4f}({v[0]})" if v else "   -          ")
        print(f"  {yr:>6d} " + " ".join(f"{s:>14s}" for s in row))

    # ── write trial + scratch JSON ─────────────────────────────────────────
    universe = sorted(common)
    universe_hash = hashlib.sha256(",".join(universe).encode()).hexdigest()
    period_start = str(closes.index.min().date())
    period_end = str(closes.index.max().date())

    param_dict = {
        "construction": "momentum_wide_target_regime_combined",
        "signal": "cross_sectional_7d_price_momentum",
        "decile_frac": DECILE_FRAC,
        "stop_atr_mult": STOP_ATR_MULT,
        "atr_window": ATR_WINDOW,
        "momentum_lookback": MOMENTUM_LOOKBACK,
        "target_r": TARGET_R,
        "taker_bps": TAKER_BPS,
        "entry_slip_bps": ENTRY_SLIP_BPS,
        "timestop_bars": TIMESTOP_BARS,
        "min_coins_day": MIN_COINS_DAY,
        "exit_resolution": "hourly_first_touch",
        "funding": "hourly_sum_as_charge_longs_pay_positive",
        "regime": "btc_200d_sma_cleaned_band_0.03",
        "zero_drift_control": "per_coin_hourly_log_return_demeaned",
        "no_lookahead": True,
        "leverage": "none_+/-1x",
        "live": "off",
    }
    param_hash = hashlib.sha256(
        json.dumps(param_dict, sort_keys=True).encode()).hexdigest()

    result = {
        "construction": param_dict["construction"],
        "target_r": TARGET_R,
        "n_coins_universe": len(universe),
        "n_trades": rs["n_trades"],
        "mean_net_r": round(rs["mean_net_r"], 6),
        "median_net_r": round(rs["median_net_r"], 6),
        "total_net_r": round(rs["total_net_r"], 6),
        "win_rate": round(rs["win_rate"], 6),
        "profit_factor": round(rs["pf"], 6),
        "mean_gross_r": round(rs["mean_gross_r"], 6),
        "mean_fee_r": round(rs["mean_fee_r"], 6),
        "mean_funding_r": round(rs["mean_funding_r"], 6),
        "exit_breakdown": rs["exit_breakdown"],
        "regime_portfolio_real": real_grid.get("regime_portfolio"),
        "regime_portfolio_control": ctrl_grid.get("regime_portfolio"),
        "control_mean_net_r": round(cs["mean_net_r"], 6),
        "regime_day_counts": {k: int(v) for k, v in rc.items()},
        "exit_resolution": "hourly_first_touch",
        "no_lookahead": True,
        "leverage": "none_+/-1x",
        "live": "off",
        "data_source": "hl_oi_hf + hl_oi_hf_clean (BTC regime) + hl_funding_hf",
    }

    if not args.no_write:
        ledger.increment_trial("HYP-24", param_hash, universe_hash,
                               period_start, period_end, result)
        print(f"\n  wrote trial HYP-24 param_hash={param_hash[:16]}...")
    else:
        print("\n  [--no-write] trial NOT written.")

    out = pathlib.Path.home() / ".hermes" / "cache" / "scratch" / "hyp24_result.json"
    payload = {
        "real": _stats(real_records),
        "control": _stats(ctrl_records),
        "compare": compare,
        "real_asset_marginal": real_grid.get("asset_marginal"),
        "control_asset_marginal": ctrl_grid.get("asset_marginal"),
        "cells_real": real_grid.get("cells"),
        "cells_control": ctrl_grid.get("cells"),
        "regime_counts": {k: int(v) for k, v in rc.items()},
        "n_trades_real": rs["n_trades"],
        "n_trades_control": cs["n_trades"],
        "real_records": [{k: r[k] for k in ("trade_date", "coin", "direction",
                                            "kind", "net_r", "risk_pct")}
                         for r in real_records],
        "ctrl_records": [{k: r[k] for k in ("trade_date", "coin", "direction",
                                            "kind", "net_r", "risk_pct")}
                         for r in ctrl_records],
    }
    with open(out, "w") as f:
        json.dump(payload, f, indent=2, default=str)
    print(f"  result saved to {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())