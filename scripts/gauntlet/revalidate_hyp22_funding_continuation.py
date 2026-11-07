"""revalidate_hyp22_funding_continuation.py — HYP-22 funding-continuation momentum.

Read-only research driver. This is the MIRROR of the failed funding-carry:
instead of FADING the funding crowd, we FOLLOW it (continuation / momentum).
Direction is exactly sign(funding): long high-positive-funding coins, short
high-negative-funding coins — a directional strategy by design (user-approved).

Pre-registered (HYP-22 frontmatter — FIXED, no tuning):
  * Signal: hourly funding_rate, resampled to daily (last rate of the day).
  * H1 (continuation is REGIME-ROBUST): conditional on extreme |funding|
    (coin's own top-decile of trailing-90d |funding| AND cross-sectional
    top-decile of |funding|), is sign(next 1-5d return) == sign(funding)?
    Reported PER REGIME (bull/flat/bear) on BTC drawdown-from-365d-high.
  * H2 (tradeable NET): long top-decile funding, short bottom-decile
    (cross-sectional, daily rebalance + 5d hold). NET = price return
    - funding PAID (follower pays |funding| on BOTH legs: longs pay positive
    funding, shorts pay negative funding) - taker fees (4.5 bps/side realistic,
    also 45 bps/side conservative).
  * ESCALATE only if H2 net > 0 under realistic cost -> G4 (CPCV 10th-pct PF)
    + G5 (DSR >= 0.95, PBO <= 0.30).

Data: hl_funding_hf (hourly funding_rate, native perps, 3.5y) + hl_oi_hf
(hourly mark_price -> daily open/close). 235 coins x ~1269 daily bars spans
2023-05 -> 2026-10 = genuinely MULTI-REGIME (2023 accumulation, 2024-25 bull,
2025Q4-2026 bear), answering what the prior ~400d slice could not.

No look-ahead: signal at day-t close (last funding of day), fill day-t+1 open.
Funding accumulated over the EXACT holding window (days t+1..t+H). No leverage
beyond +-1x spread. LIVE off. Cost charged once. Writes ONE trials-ledger entry
(fresh param_hash). Path-scoped commit (never git add -A/.).

Usage: python3 revalidate_hyp22_funding_continuation.py [--no-write]
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

import trials_ledger as ledger                              # noqa: E402
import cpcv_harness as cpcv                                  # noqa: E402

FUNDING_DIR = pathlib.Path.home() / ".hermes" / "market_data" / "hl_funding_hf"
OI_DIR = pathlib.Path.home() / ".hermes" / "market_data" / "hl_oi_hf"

# ── Pre-registered constants (FIXED — do not tune) ──────────────────────────
PCTILE = 90.0                 # top-decile threshold (both axes)
TRAIL_WINDOW_DAYS = 90        # coin's own trailing-90d |funding| window
FORWARD_BARS = 5              # H1 1-5d forward horizons
DECILE_FRAC = 0.10            # H2 cross-sectional decile
MIN_COINS_DAY = 20            # require >= this many ranked coins to form a day
HOLD_PRIMARY = 1              # daily rebalance
HOLD_5D = 5                   # 5d hold
TAKER_BPS_REAL = 4.5          # realistic taker, per side (fill)
TAKER_BPS_CONSERVATIVE = 45.0  # fail-closed taker, per side (fill)
N_GROUPS = 12                 # CPCV chronological groups
K_TEST = 2                    # CPCV test groups per split

# Regime classification: BTC drawdown from trailing-365d running max.
REGIME_BULL_DD = -0.10        # dd >= -10%  -> bull (near highs)
REGIME_BEAR_DD = -0.25        # dd <  -25%  -> bear (deep correction)


# ────────────────────────────────────────────────────────────────────────────
def load_funding_daily() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Hourly funding -> daily (last-rate signal panel, sum-of-hourly panel).

    Returns (fund_last, fund_sum), each date-indexed, columns=coins.
    """
    files = sorted(glob.glob(str(FUNDING_DIR / "*.parquet")))
    if not files:
        raise SystemExit(f"no funding parquet under {FUNDING_DIR}")
    cols = ["timestamp", "coin", "dex", "funding_rate"]
    parts = [pd.read_parquet(f, columns=cols) for f in files]
    df = pd.concat(parts, ignore_index=True)
    native = df[df["dex"] == ""].dropna(subset=["funding_rate"])
    native["timestamp"] = native["timestamp"].dt.tz_convert("UTC")
    native["date"] = native["timestamp"].dt.normalize()

    g = (native.sort_values("timestamp")
         .groupby(["coin", "date"], sort=False)
         .agg(last=("funding_rate", "last"), total=("funding_rate", "sum"))
         .reset_index())

    start = g["date"].min()
    end = g["date"].max()
    cal = pd.date_range(start, end, freq="D", tz="UTC")
    fund_last = g.pivot(index="date", columns="coin", values="last").reindex(cal)
    fund_sum = g.pivot(index="date", columns="coin", values="total").reindex(cal)
    return fund_last, fund_sum


def load_oi_daily() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Hourly mark_price -> daily (open, close) panels (native perps)."""
    files = sorted(glob.glob(str(OI_DIR / "*.parquet")))
    if not files:
        raise SystemExit(f"no OI parquet under {OI_DIR}")
    cols = ["timestamp", "coin", "dex", "mark_price"]
    parts = [pd.read_parquet(f, columns=cols) for f in files]
    df = pd.concat(parts, ignore_index=True)
    native = df[df["dex"] == ""].dropna(subset=["mark_price"])
    native["timestamp"] = native["timestamp"].dt.tz_convert("UTC")
    native["date"] = native["timestamp"].dt.normalize()

    daily = (native.sort_values("timestamp")
             .groupby(["coin", "date"], sort=False)
             .agg(open=("mark_price", "first"), close=("mark_price", "last"))
             .reset_index())

    start = daily["date"].min()
    end = daily["date"].max()
    cal = pd.date_range(start, end, freq="D", tz="UTC")
    opens = daily.pivot(index="date", columns="coin", values="open").reindex(cal)
    closes = daily.pivot(index="date", columns="coin", values="close").reindex(cal)
    return opens, closes


def btc_regime(closes: pd.DataFrame) -> pd.Series:
    """Per-date regime from BTC drawdown-from-trailing-365d-max.

    Returns a Series indexed by date: 'bull' / 'flat' / 'bear'.
    """
    btc = closes["BTC"].astype(float)
    rm = btc.rolling(365, min_periods=30).max()
    dd = btc / rm - 1.0
    regime = pd.Series("flat", index=closes.index)
    regime[dd >= REGIME_BULL_DD] = "bull"
    regime[dd < REGIME_BEAR_DD] = "bear"
    return regime


def _pf(rs) -> float:
    gains = sum(r for r in rs if r > 0)
    losses = abs(sum(r for r in rs if r < 0))
    return gains / losses if losses > 0 else (float("inf") if gains > 0 else 0.0)


# ────────────────────────────────────────────────────────────────────────────
# H1 — extreme |funding| -> continuation, per regime
# ────────────────────────────────────────────────────────────────────────────
def h1_events(fund_last: pd.DataFrame, closes: pd.DataFrame,
              regime: pd.Series) -> pd.DataFrame:
    """Extreme |funding| events (own-90d top-decile AND xs top-decile).

    Returns a DataFrame of events with directional forward returns (h=1..5)
    and the regime label.
    """
    absf = fund_last.abs()
    # coin's own trailing-90d 90th-pct of |funding| (full 90d window required)
    own_p90 = absf.rolling(TRAIL_WINDOW_DAYS,
                           min_periods=TRAIL_WINDOW_DAYS).quantile(PCTILE / 100.0)

    # forward returns close-to-close over h=1..5
    fwd = {}
    for h in range(1, FORWARD_BARS + 1):
        fwd[h] = closes.shift(-h) / closes - 1.0

    common = fund_last.index.intersection(closes.index)
    events: list[dict] = []
    dates = list(common)
    # precompute cross-sectional P90 of |funding| per day
    for t in range(len(dates) - FORWARD_BARS):
        d = dates[t]
        row = absf.loc[d].to_numpy(dtype=float)
        own = own_p90.loc[d].to_numpy(dtype=float)
        sign_row = fund_last.loc[d].to_numpy(dtype=float)
        reg = regime.loc[d]
        valid = np.isfinite(row) & np.isfinite(own) & np.isfinite(sign_row)
        if valid.sum() < MIN_COINS_DAY:
            continue
        xs_p90 = float(np.percentile(row[valid], PCTILE))
        for i in np.where(valid)[0]:
            # own top-decile AND cross-sectional top-decile of |funding|
            if not (row[i] >= own[i] and row[i] >= xs_p90):
                continue
            sg = 1.0 if sign_row[i] > 0 else (-1.0 if sign_row[i] < 0 else 0.0)
            if sg == 0.0:
                continue
            ev = {"date": d, "coin": closes.columns[i], "sign": sg,
                  "funding": float(sign_row[i]), "abs_funding": float(row[i]),
                  "regime": reg}
            for h in range(1, FORWARD_BARS + 1):
                f = closes.iloc[t + h, i]
                c0 = closes.iloc[t, i]
                if pd.isna(f) or pd.isna(c0) or c0 == 0:
                    ev[f"fwd{h}"] = np.nan
                else:
                    ev[f"fwd{h}"] = float(f / c0 - 1.0)
            events.append(ev)
    return pd.DataFrame(events)


# ────────────────────────────────────────────────────────────────────────────
# H2 — cross-sectional signed-funding spread, net of funding + fees
# ────────────────────────────────────────────────────────────────────────────
def h2_spread(fund_last: pd.DataFrame, fund_sum: pd.DataFrame,
              opens: pd.DataFrame, hold: int) -> dict:
    """Long top-decile (funding), short bottom-decile; net of funding + fees.

    Follows the HYP-21 no-lookahead convention: signal close[t], fill open[t+1],
    exit open[t+1+hold]. Funding = sum of hourly funding over days t+1..t+hold.

    Returns per-rebalance records with full decomposition (gross price, funding
    long/short, net at both fee tiers).
    """
    cols = [c for c in fund_last.columns if c in opens.columns]
    sig = fund_last[cols]
    fsum = fund_sum[cols]
    opens_sub = opens[cols]

    entry = opens_sub.shift(-1)
    exitp = opens_sub.shift(-(1 + hold))
    fwd = exitp / entry - 1.0

    # funding accumulated over the exact hold window (days t+1 .. t+hold)
    fund_shift = fsum.shift(-1)                       # [t] = sum_funding[t+1]
    fund_hold = fund_shift.rolling(hold, min_periods=hold).sum()  # sum days t+1..t+hold

    common = sig.index.intersection(opens_sub.index)
    sig = sig.loc[common]
    fwd = fwd.loc[common]
    fund_hold = fund_hold.loc[common]

    fee_real = 4 * TAKER_BPS_REAL / 1e4          # 2 legs x 2 fills
    fee_cons = 4 * TAKER_BPS_CONSERVATIVE / 1e4

    records: list[dict] = []
    dates = list(sig.index)
    for t in range(len(dates) - (1 + hold)):
        s = sig.iloc[t].to_numpy(dtype=float)
        f = fwd.iloc[t].to_numpy(dtype=float)
        fh = fund_hold.iloc[t].to_numpy(dtype=float)
        mask = np.isfinite(s) & np.isfinite(f) & np.isfinite(fh)
        if mask.sum() < MIN_COINS_DAY:
            continue
        s_v, f_v, fh_v = s[mask], f[mask], fh[mask]
        order = np.argsort(s_v)
        n = len(s_v)
        k = max(1, n // 10)                        # top/bottom decile
        bot_idx = order[:k]
        top_idx = order[-k:]

        long_ret = float(np.mean(f_v[top_idx]))          # price return long leg
        short_ret = float(np.mean(f_v[bot_idx]))         # price return shorted coins
        gross = long_ret - short_ret                     # momentum spread (price only)

        # funding the follower PAYS (|funding| on both legs)
        long_fund = float(np.mean(fh_v[top_idx]))        # >0 -> longs pay
        short_fund = float(np.mean(-fh_v[bot_idx]))      # >0 -> shorts pay (fund<0)
        fund_cost = long_fund + short_fund

        net_real = gross - fund_cost - fee_real
        net_cons = gross - fund_cost - fee_cons
        records.append({
            "date": dates[t], "n": n, "k": k,
            "long_ret": long_ret, "short_ret": short_ret, "gross": gross,
            "long_fund": long_fund, "short_fund": short_fund, "fund_cost": fund_cost,
            "net_real": net_real, "net_cons": net_cons,
            "mean_long_funding_signal": float(np.mean(s_v[top_idx])),
            "mean_short_funding_signal": float(np.mean(s_v[bot_idx])),
        })

    return {"hold": hold, "records": records,
            "fee_real_bps": fee_real * 1e4, "fee_cons_bps": fee_cons * 1e4}


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
    """G4 (CPCV split-PF) + G5 (DSR, PBO) on a non-overlapping NET series."""
    pnl_bps = [n * 1e4 for n in nets]
    trades = [{"entry_time": int(i), "exit_time": int(i) + hold,
               "pnl_bps": float(p)} for i, p in enumerate(pnl_bps)]
    res = cpcv.run_cpcv(trades, n_groups=N_GROUPS, k_test=K_TEST,
                        n_trials_from_ledger=ledger_n,
                        holding_horizon_bars=hold, embargo_bars=hold)
    split_pfs = [m["pf"] for m in res["split_metrics"] if m["trade_count"] > 0]
    pct10_pf = float(np.percentile(split_pfs, 10)) if split_pfs else float("nan")
    med_pf = float(np.median(split_pfs)) if split_pfs else float("nan")

    arr = np.asarray(pnl_bps, dtype=float)
    sharpe, skew, kurt, _ = _moments(arr)
    dsr = cpcv.compute_dsr(sharpe, skew, kurt, max(1, ledger_n), len(arr))
    return {
        "pbo": res["pbo"],
        "dsr": dsr,
        "sharpe_nonoverlap": round(sharpe, 6),
        "split_median_pf": round(med_pf, 4),
        "split_pct10_pf": round(pct10_pf, 4),
        "n_obs_nonoverlap": len(arr),
        "n_trials": ledger_n,
    }


def _summary_h2(res: dict, key: str, hold: int) -> dict:
    recs = res["records"]
    stride = 1 if hold <= 1 else hold
    nets = [recs[i][key] for i in range(0, len(recs), stride)]
    arr = np.asarray([r[key] for r in recs])
    fund_arr = np.asarray([r["fund_cost"] for r in recs])
    gross_arr = np.asarray([r["gross"] for r in recs])
    mean_long_sig = float(np.mean([r["mean_long_funding_signal"] for r in recs]))
    mean_short_sig = float(np.mean([r["mean_short_funding_signal"] for r in recs]))
    return {
        "hold": hold, "n_rebalances": len(recs),
        "mean_n_coins": float(np.mean([r["n"] for r in recs])),
        "mean_k_per_leg": float(np.mean([r["k"] for r in recs])),
        "mean_gross_bps": round(float(gross_arr.mean()) * 1e4, 4),
        "mean_fund_cost_bps": round(float(fund_arr.mean()) * 1e4, 4),
        "mean_long_funding_signal_bps": round(mean_long_sig * 1e4, 4),
        "mean_short_funding_signal_bps": round(mean_short_sig * 1e4, 4),
        "mean_net_bps": round(float(arr.mean()) * 1e4, 4),
        "mean_net_nonoverlap_bps": round(float(np.mean(nets)) * 1e4, 4),
        "win_rate_net": round(float((arr > 0).mean()), 6),
        "pf_net": round(_pf(arr.tolist()), 6),
    }


# ────────────────────────────────────────────────────────────────────────────
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-write", action="store_true")
    args = ap.parse_args()

    print("=== HYP-22 funding-continuation momentum (directional) — real data ===\n")

    # ── load panels ──────────────────────────────────────────────────────────
    print("loading hourly funding -> daily last/sum panels ...")
    fund_last, fund_sum = load_funding_daily()
    print(f"  funding panel: {fund_last.shape[0]} days x {fund_last.shape[1]} coins "
          f"({fund_last.index.min().date()} -> {fund_last.index.max().date()})")

    # degeneracy diagnostic (the known HYP-20/21 issue)
    fr = fund_last.to_numpy(dtype=float)
    fr = fr[np.isfinite(fr)]
    modal = float(pd.Series(fr).mode().iloc[0])
    frac_modal = float((np.abs(fr - modal) < 1e-12).mean())
    above_modal_per_day = (fund_last > modal + 1e-12).sum(axis=1)
    print(f"  funding degeneracy: {frac_modal*100:.1f}% daily cells pinned at modal "
          f"{modal:.2e}/hr; median {float(above_modal_per_day.median()):.0f} coins/day "
          f"genuinely above modal")

    print("loading hourly mark -> daily open/close panels ...")
    opens, closes = load_oi_daily()
    print(f"  OI panel: {opens.shape[0]} days x {opens.shape[1]} coins "
          f"({opens.index.min().date()} -> {opens.index.max().date()})")

    common_cols = [c for c in fund_last.columns if c in opens.columns]
    print(f"  intersection coins: {len(common_cols)}")

    regime = btc_regime(closes)
    reg_counts = regime.value_counts()
    print(f"  regime split (BTC dd from 365d high): "
          f"bull {reg_counts.get('bull',0)}, flat {reg_counts.get('flat',0)}, "
          f"bear {reg_counts.get('bear',0)} days")

    # ── H1 ───────────────────────────────────────────────────────────────────
    print("\n===== H1 — is funding->continuation REGIME-ROBUST? =====")
    ev = h1_events(fund_last, closes, regime)
    print(f"  extreme-|funding| events (own-90d p90 AND xs p90): {len(ev)}")
    if ev.empty:
        print("  no events — aborting")
        return 1
    print(f"  event ts range: {ev['date'].min().date()} -> {ev['date'].max().date()}")

    h1_rows = {}
    for reg in ("bull", "flat", "bear"):
        sub = ev[ev["regime"] == reg]
        row = {"n": int(len(sub))}
        for h in range(1, FORWARD_BARS + 1):
            dirret = sub["sign"] * sub[f"fwd{h}"]
            dirret = dirret.dropna()
            if len(dirret):
                row[f"h{h}_hitrate"] = float((dirret > 0).mean())
                row[f"h{h}_mean_dir_bps"] = float(dirret.mean() * 1e4)
            else:
                row[f"h{h}_hitrate"] = float("nan")
                row[f"h{h}_mean_dir_bps"] = float("nan")
        h1_rows[reg] = row

    print(f"  {'regime':6s} {'n':>6s} | " +
          " | ".join(f"h{h} hit-rate  h{h} dir(bps)" for h in range(1, FORWARD_BARS + 1)))
    for reg in ("bull", "flat", "bear"):
        r = h1_rows[reg]
        cells = []
        for h in range(1, FORWARD_BARS + 1):
            cells.append(f"{r[f'h{h}_hitrate']:.3f}  {r[f'h{h}_mean_dir_bps']:+.1f}")
        print(f"  {reg:6s} {r['n']:6d} | " + "  |  ".join(cells))
    print("  (hit-rate = P(sign(fwd) == sign(funding)); dir bps = mean(sign*fwd)*1e4)")

    # pooled (all regimes) for reference
    pooled = {}
    for h in range(1, FORWARD_BARS + 1):
        dirret = (ev["sign"] * ev[f"fwd{h}"]).dropna()
        pooled[h] = dirret.mean() * 1e4
    print(f"  POOLED mean dir return (bps): "
          + " ".join(f"h{h}={pooled[h]:+.1f}" for h in range(1, FORWARD_BARS + 1)))

    # ── H2 ───────────────────────────────────────────────────────────────────
    print("\n===== H2 — tradeable NET (long top-decile, short bottom-decile) =====")
    print(f"  fee model: taker {TAKER_BPS_REAL}b/side (realistic) or "
          f"{TAKER_BPS_CONSERVATIVE}b/side (fail-closed); spread = 2 legs x 2 fills")

    ledger_n = ledger.count()
    h2 = {}
    for hold in (HOLD_PRIMARY, HOLD_5D):
        res = h2_spread(fund_last, fund_sum, opens, hold)
        s_real = _summary_h2(res, "net_real", hold) if res["records"] else None
        s_cons = _summary_h2(res, "net_cons", hold) if res["records"] else None
        h2[hold] = {"res": res, "real": s_real, "cons": s_cons}

        if not res["records"]:
            print(f"  hold={hold}d: no rebalances")
            continue
        print(f"\n  --- hold={hold}d (daily rebalance{' + 5d hold' if hold>1 else ''}) ---")
        print(f"    n_rebalances={s_real['n_rebalances']}  mean_n_coins={s_real['mean_n_coins']:.0f}  "
              f"k/leg={s_real['mean_k_per_leg']:.0f}")
        print(f"    mean funding SIGNAL (bps/hr): long leg {s_real['mean_long_funding_signal_bps']:+.2f}  "
              f"short leg {s_real['mean_short_funding_signal_bps']:+.2f}")
        print(f"    GROSS price spread : {s_real['mean_gross_bps']:+.2f} bps/reb")
        print(f"    funding PAID       : {s_real['mean_fund_cost_bps']:+.2f} bps/reb "
              f"(long {float(np.mean([r['long_fund'] for r in res['records']]))*1e4:+.2f} + "
              f"short {float(np.mean([r['short_fund'] for r in res['records']]))*1e4:+.2f})")
        print(f"    fee (2 legs)       : {res['fee_real_bps']:.1f} bps (real) / "
              f"{res['fee_cons_bps']:.1f} bps (cons)")
        print(f"    NET @real 4.5b     : {s_real['mean_net_bps']:+.2f} bps/reb   "
              f"(non-overlap {s_real['mean_net_nonoverlap_bps']:+.2f})   "
              f"win {s_real['win_rate_net']:.3f}  PF {s_real['pf_net']:.3f}")
        print(f"    NET @cons 45b      : {s_cons['mean_net_bps']:+.2f} bps/reb")

        # robustness only if net > 0 under realistic cost
        if s_real["mean_net_bps"] > 0:
            recs = res["records"]
            stride = 1 if hold <= 1 else hold
            nets = [recs[i]["net_real"] for i in range(0, len(recs), stride)]
            rob = robustness(nets, hold, ledger_n)
            h2[hold]["robustness"] = rob
            print(f"    G4/G5 @real: n_obs={rob['n_obs_nonoverlap']}  "
                  f"splitPF med={rob['split_median_pf']} P10={rob['split_pct10_pf']}  "
                  f"PBO={rob['pbo']}  DSR={rob['dsr']}  sharpe={rob['sharpe_nonoverlap']}")
        else:
            print(f"    [net <= 0 at real cost -> NO escalation per kill rule]")

    # ── write trial ──────────────────────────────────────────────────────────
    universe = sorted(common_cols)
    universe_hash = hashlib.sha256(",".join(universe).encode()).hexdigest()
    period_start = str(fund_last.index.min().date())
    period_end = str(fund_last.index.max().date())

    param_dict = {
        "construction": "funding_continuation_momentum",
        "direction": "follow_crowd_sign_funding",
        "signal": "daily_last_funding_rate",
        "pctile": PCTILE,
        "trail_window_days": TRAIL_WINDOW_DAYS,
        "forward_bars": FORWARD_BARS,
        "decile_frac": DECILE_FRAC,
        "min_coins_day": MIN_COINS_DAY,
        "taker_bps_realistic": TAKER_BPS_REAL,
        "taker_bps_conservative": TAKER_BPS_CONSERVATIVE,
        "fee_model": "4_fills_per_spread_rebalance",
        "funding_cost": "sum_funding_rate_over_holding_window",
        "regime": "btc_drawdown_365d",
        "regime_bull_dd": REGIME_BULL_DD,
        "regime_bear_dd": REGIME_BEAR_DD,
        "no_lookahead": True,
        "leverage": "none_+/-1x_spread",
        "live": "off",
    }
    param_hash = hashlib.sha256(
        json.dumps(param_dict, sort_keys=True).encode()).hexdigest()

    result = {
        "construction": "funding_continuation_momentum",
        "direction": "follow_crowd_sign_funding",
        "n_coins_universe": len(universe),
        "funding_degeneracy_frac_at_modal": round(frac_modal, 4),
        "funding_modal_rate": modal,
        "median_coins_above_modal_per_day": float(above_modal_per_day.median()),
        "regime_counts": {k: int(v) for k, v in reg_counts.items()},
        "h1": {
            "n_events": int(len(ev)),
            "per_regime": h1_rows,
            "pooled_dir_bps": {f"h{h}": round(pooled[h], 4) for h in range(1, FORWARD_BARS + 1)},
        },
        "hold_1d": {
            "gross_bps": h2[HOLD_PRIMARY]["real"]["mean_gross_bps"],
            "fund_cost_bps": h2[HOLD_PRIMARY]["real"]["mean_fund_cost_bps"],
            "net_real_45bps_bps": h2[HOLD_PRIMARY]["real"]["mean_net_bps"],
            "net_cons_45bps_bps": h2[HOLD_PRIMARY]["cons"]["mean_net_bps"],
            "net_real_nonoverlap_bps": h2[HOLD_PRIMARY]["real"]["mean_net_nonoverlap_bps"],
            "n_rebalances": h2[HOLD_PRIMARY]["real"]["n_rebalances"],
        },
        "hold_5d": {
            "gross_bps": h2[HOLD_5D]["real"]["mean_gross_bps"],
            "fund_cost_bps": h2[HOLD_5D]["real"]["mean_fund_cost_bps"],
            "net_real_45bps_bps": h2[HOLD_5D]["real"]["mean_net_bps"],
            "net_cons_45bps_bps": h2[HOLD_5D]["cons"]["mean_net_bps"],
            "net_real_nonoverlap_bps": h2[HOLD_5D]["real"]["mean_net_nonoverlap_bps"],
            "n_rebalances": h2[HOLD_5D]["real"]["n_rebalances"],
        },
        "robustness": {str(h): h2[h].get("robustness")
                       for h in (HOLD_PRIMARY, HOLD_5D) if h2[h]["res"]["records"]},
        "no_lookahead": True,
        "leverage": "none_+/-1x_spread",
        "live": "off",
        "data_source": "hl_funding_hf + hl_oi_hf parquet (native perps, 3.5y)",
    }

    if not args.no_write:
        e = ledger.increment_trial("HYP-22", param_hash, universe_hash,
                                   period_start, period_end, result)
        print(f"\nwrote trial HYP-22  param_hash={e['param_hash'][:16]}...  "
              f"chain_hash={e['chain_hash'][:16]}...  ledger_N={ledger_n + 1}")
    else:
        print(f"\n[--no-write] trial NOT written. param_hash={param_hash[:16]}...")

    # dump result JSON for the report
    out = pathlib.Path.home() / ".hermes" / "cache" / "scratch" / "hyp22_result.json"
    with open(out, "w") as f:
        json.dump(result, f, indent=2, default=str)
    print(f"result saved to {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())